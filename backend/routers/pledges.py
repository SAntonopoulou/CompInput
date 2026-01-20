import stripe
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import logging
import traceback
import os

from ..database import get_session
from ..models import Pledge, Project, User, PledgeStatus, ProjectStatus, Notification
from ..deps import get_current_user
from ..security import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/pledges", tags=["pledges"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PledgeRequest(BaseModel):
    project_id: int
    amount: int

class PledgeRead(BaseModel):
    id: int
    amount: int
    status: PledgeStatus
    created_at: datetime
    project_id: int
    project_title: str
    project_status: ProjectStatus

    class Config:
        from_attributes = True

class PublicPledgeHistory(BaseModel):
    project_id: int
    project_title: str
    created_at: datetime

@router.post("/", status_code=201)
def create_pledge_checkout_session(
    pledge_in: PledgeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Phase 1: Create a PENDING pledge and a Stripe Checkout Session.
    """
    project = session.get(Project, pledge_in.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status != ProjectStatus.FUNDING:
        raise HTTPException(status_code=400, detail="Project is not active for funding")

    # Create a pending pledge record
    pending_pledge = Pledge(
        user_id=current_user.id,
        project_id=project.id,
        amount=pledge_in.amount,
        status=PledgeStatus.PENDING
    )
    session.add(pending_pledge)
    session.commit()
    session.refresh(pending_pledge)

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Pledge for '{project.title}'",
                    },
                    'unit_amount': pledge_in.amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{FRONTEND_URL}/student/dashboard?payment=success",
            cancel_url=f"{FRONTEND_URL}/projects/{project.id}?payment=cancelled",
            client_reference_id=str(pending_pledge.id) # Link our pledge to the Stripe session
        )
        
        # Save the checkout session ID to our pledge record
        pending_pledge.checkout_session_id = checkout_session.id
        session.add(pending_pledge)
        session.commit()

        return {"checkout_url": checkout_session.url}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error during checkout session creation: {e}")
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=List[PledgeRead])
def list_my_pledges(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Pledge).where(Pledge.user_id == current_user.id).options(selectinload(Pledge.project)).order_by(Pledge.created_at.desc())
    pledges = session.exec(statement).all()
    
    results = []
    for p in pledges:
        project_title = p.project.title if p.project else "Unknown Project"
        project_status = p.project.status if p.project else ProjectStatus.CANCELLED
        
        results.append(PledgeRead(
            id=p.id,
            amount=p.amount,
            status=p.status,
            created_at=p.created_at,
            project_id=p.project_id,
            project_title=project_title,
            project_status=project_status
        ))
    return results

@router.get("/user/{user_id}", response_model=List[PublicPledgeHistory])
def get_user_pledges(
    user_id: int,
    session: Session = Depends(get_session)
):
    statement = select(Pledge).where(Pledge.user_id == user_id).options(selectinload(Pledge.project)).order_by(Pledge.created_at.desc())
    pledges = session.exec(statement).all()
    
    results = []
    for p in pledges:
        if p.project:
            results.append(PublicPledgeHistory(project_id=p.project_id, project_title=p.project.title, created_at=p.created_at))
    return results

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    session: Session = Depends(get_session)
):
    logger.info("Webhook endpoint hit.")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("⚠️ Webhook payload parsing failed.")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("⚠️ Webhook signature verification failed. Check your STRIPE_WEBHOOK_SECRET in the .env file.")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event['type']
    data = event['data']['object']
    logger.info(f"Received event: {event_type}")

    if event_type == 'checkout.session.completed':
        session_obj = data
        client_reference_id = session_obj.get('client_reference_id')

        if not client_reference_id:
            logger.error("Webhook error: checkout.session.completed event is missing 'client_reference_id'.")
            return {"status": "error", "detail": "Missing client_reference_id"}

        try:
            pledge_id = int(client_reference_id)
            logger.info(f"Processing pledge_id: {pledge_id} from client_reference_id.")
            
            pledge = session.get(Pledge, pledge_id)
            if not pledge or pledge.status != PledgeStatus.PENDING:
                status = pledge.status if pledge else 'Not Found'
                logger.warning(f"Webhook for non-pending or non-existent pledge ID: {pledge_id}. Status: {status}")
                return {"status": "success", "detail": "Pledge not found or already processed"}

            logger.info(f"Found pending pledge {pledge.id}. Updating status to CAPTURED.")
            pledge.status = PledgeStatus.CAPTURED
            pledge.payment_intent_id = session_obj.get('payment_intent')
            
            project = session.get(Project, pledge.project_id)
            if project:
                logger.info(f"Updating project {project.id}. Current funding: {project.current_funding}. Pledge amount: {pledge.amount}")
                project.current_funding += pledge.amount
                logger.info(f"New project funding: {project.current_funding}")
                session.add(project) # Explicitly add to session to track changes
                
                notification = Notification(
                    user_id=project.teacher_id,
                    content=f"You received a new pledge of ${pledge.amount/100:.2f} for your project '{project.title}'!",
                    link=f"/projects/{project.id}"
                )
                session.add(notification)

                if project.current_funding >= project.funding_goal and project.status == ProjectStatus.FUNDING:
                    project.status = ProjectStatus.SUCCESSFUL
                    logger.info(f"Project {project.id} has been fully funded.")
                    goal_notification = Notification(
                        user_id=project.teacher_id,
                        content=f"Congratulations! Your project '{project.title}' has been fully funded!",
                        link=f"/projects/{project.id}"
                    )
                    session.add(goal_notification)
            else:
                logger.error(f"CRITICAL: Could not find project with ID {pledge.project_id} for pledge {pledge.id}")
            
            session.commit()
            logger.info(f"Successfully captured and committed pledge {pledge_id}")
        except Exception as e:
            logger.error(f"Error processing checkout.session.completed for pledge_id {client_reference_id}: {e}\n{traceback.format_exc()}")
            session.rollback()

    elif event_type == 'account.updated':
        try:
            account = data
            stripe_account_id = account['id']
            
            teacher = session.exec(select(User).where(User.stripe_account_id == stripe_account_id)).first()
            if teacher:
                teacher.charges_enabled = account['charges_enabled']
                teacher.payouts_enabled = account['payouts_enabled']
                
                if not teacher.charges_enabled:
                    projects_to_hold = session.exec(select(Project).where(Project.teacher_id == teacher.id, Project.status == ProjectStatus.FUNDING)).all()
                    for proj in projects_to_hold:
                        proj.status = ProjectStatus.ON_HOLD
                
                notification = Notification(
                    user_id=teacher.id,
                    content="Your Stripe account status has been updated. Please check your Stripe Dashboard for details.",
                    link="/teacher/dashboard"
                )
                session.add(notification)
                session.commit()
                logger.info(f"Updated Stripe account status for teacher {teacher.id}")
        except Exception as e:
            logger.error(f"Error processing account.updated: {e}\n{traceback.format_exc()}")
            session.rollback()

    elif event_type == 'charge.refunded':
        try:
            charge = data
            payment_intent_id = charge['payment_intent']
            
            pledge_to_refund = session.exec(select(Pledge).where(Pledge.payment_intent_id == payment_intent_id)).first()
            if pledge_to_refund and pledge_to_refund.status != PledgeStatus.REFUNDED:
                pledge_to_refund.status = PledgeStatus.REFUNDED
                
                project = session.get(Project, pledge_to_refund.project_id)
                if project:
                    project.current_funding -= pledge_to_refund.amount
                
                session.commit()
                logger.info(f"Processed refund for pledge {pledge_to_refund.id}")
        except Exception as e:
            logger.error(f"Error processing charge.refunded: {e}\n{traceback.format_exc()}")
            session.rollback()

    else:
        logger.info(f"Unhandled event type: {event_type}")

    return {"status": "success"}
