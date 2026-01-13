import stripe
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..database import get_session
from ..models import Pledge, Project, User, PledgeStatus, ProjectStatus, Notification
from ..deps import get_current_user
from ..security import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/pledges", tags=["pledges"])

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
def create_pledge(
    pledge_in: PledgeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Initiate a pledge. Creates a Stripe PaymentIntent and a local Pledge record.
    """
    project = session.get(Project, pledge_in.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status != ProjectStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Project is not active for funding")

    # Create Stripe PaymentIntent
    try:
        intent = stripe.PaymentIntent.create(
            amount=pledge_in.amount,
            currency="usd", # Could be dynamic based on user preference
            metadata={"project_id": project.id, "user_id": current_user.id},
            automatic_payment_methods={"enabled": True},
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create Local Pledge
    pledge = Pledge(
        user_id=current_user.id,
        project_id=project.id,
        amount=pledge_in.amount,
        status=PledgeStatus.PENDING,
        stripe_payment_intent_id=intent.id
    )
    session.add(pledge)
    session.commit()
    session.refresh(pledge)

    return {"client_secret": intent.client_secret, "pledge_id": pledge.id}

@router.get("/me", response_model=List[PledgeRead])
def list_my_pledges(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Pledge).where(Pledge.user_id == current_user.id).options(selectinload(Pledge.project)).order_by(Pledge.created_at.desc())
    pledges = session.exec(statement).all()
    
    results = []
    for p in pledges:
        # Handle potential missing project (though unlikely with FK)
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
    """
    Get public history of projects funded by a specific user.
    """
    statement = select(Pledge).where(Pledge.user_id == user_id).options(selectinload(Pledge.project)).order_by(Pledge.created_at.desc())
    pledges = session.exec(statement).all()
    
    results = []
    for p in pledges:
        if p.project: # Only show if project still exists
            results.append(PublicPledgeHistory(project_id=p.project_id, project_title=p.project.title, created_at=p.created_at))
    return results

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    session: Session = Depends(get_session)
):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        stripe_pi_id = payment_intent["id"]
        
        # Find the pledge
        statement = select(Pledge).where(Pledge.stripe_payment_intent_id == stripe_pi_id)
        pledge = session.exec(statement).first()
        
        if pledge and pledge.status != PledgeStatus.CAPTURED:
            # 1. Mark Pledge as Captured
            pledge.status = PledgeStatus.CAPTURED
            session.add(pledge)
            
            # 2. Update Project Amount
            project = session.exec(select(Project).where(Project.id == pledge.project_id)).one()
            project.current_amount += pledge.amount
            
            if project.current_amount >= project.goal_amount and project.status == ProjectStatus.ACTIVE:
                project.status = ProjectStatus.FUNDED
                
                # Calculate actual deadline based on delivery_days
                if project.delivery_days:
                    project.deadline = datetime.utcnow() + timedelta(days=project.delivery_days)
                
                # NOTIFICATION: Notify Teacher
                notification = Notification(
                    user_id=project.teacher_id,
                    content=f"Your project '{project.title}' has been fully funded!",
                    is_read=False,
                    link=f"/projects/{project.id}"
                )
                session.add(notification)
            
            session.add(project)
            session.commit()
            
    return {"status": "success"}
