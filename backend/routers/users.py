import stripe
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import User, UserRole
from ..security import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/users", tags=["users"])

class OnboardingRequest(BaseModel):
    country: str = "US" # Default to US, but allows JP, FR, ES, etc.

class OnboardingResponse(BaseModel):
    url: str

class TeacherRead(BaseModel):
    id: int
    full_name: str

@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user details.
    """
    return current_user

@router.get("/teachers", response_model=List[TeacherRead])
def search_teachers(
    query: str = Query(..., min_length=1),
    session: Session = Depends(get_session)
):
    """
    Search for teachers by name.
    """
    statement = select(User).where(User.role == UserRole.TEACHER).where(User.full_name.ilike(f"%{query}%"))
    teachers = session.exec(statement).all()
    return [TeacherRead(id=t.id, full_name=t.full_name) for t in teachers]

@router.post("/onboard", response_model=OnboardingResponse)
def onboard_teacher(
    onboarding_in: OnboardingRequest = OnboardingRequest(),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a Stripe Connect account for the teacher and return the onboarding link.
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can onboard with Stripe",
        )
    
    try:
        # 1. Create Stripe Account if not exists
        if not current_user.stripe_account_id:
            account = stripe.Account.create(
                type="express",
                country=onboarding_in.country,
                email=current_user.email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
            )
            current_user.stripe_account_id = account.id
            session.add(current_user)
            session.commit()
            session.refresh(current_user)
        
        # 2. Create Account Link
        # Use environment variable for production, fallback to localhost for dev
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")
        account_link = stripe.AccountLink.create(
            account=current_user.stripe_account_id,
            refresh_url=f"{frontend_url}/teacher/dashboard",
            return_url=f"{frontend_url}/teacher/dashboard",
            type="account_onboarding",
        )
        
        return {"url": account_link.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
