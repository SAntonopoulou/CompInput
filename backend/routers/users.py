import stripe
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import User, UserRole, Project, Pledge, Request, ProjectStatus, ProjectRating
from ..security import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

router = APIRouter(prefix="/users", tags=["users"])

class OnboardingResponse(BaseModel):
    onboarding_url: str

class TeacherRead(BaseModel):
    id: int
    full_name: str

class UserProfile(BaseModel):
    id: int
    full_name: str
    bio: Optional[str]
    languages: Optional[str]
    role: UserRole
    created_at: str
    average_rating: Optional[float] = None
    intro_video_url: Optional[str] = None
    sample_video_url: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[str] = None
    intro_video_url: Optional[str] = None
    sample_video_url: Optional[str] = None
    avatar_url: Optional[str] = None

@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=User)
def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user_data = user_in.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(current_user, key, value)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    deleted_user = session.exec(select(User).where(User.email == "deleted@system")).first()
    if not deleted_user:
        # This is a fallback, should ideally be seeded
        deleted_user = User(email="deleted@system", hashed_password="deleted", full_name="Deleted User", role=UserRole.STUDENT)
        session.add(deleted_user)
        session.commit()
        session.refresh(deleted_user)
    
    # Reassign projects, pledges, requests
    for project in current_user.taught_projects:
        project.teacher_id = deleted_user.id
    for pledge in current_user.pledges:
        pledge.user_id = deleted_user.id
    for request in current_user.requests:
        request.user_id = deleted_user.id

    session.delete(current_user)
    session.commit()
    return

@router.get("/{user_id}/profile", response_model=UserProfile)
def get_user_profile(
    user_id: int,
    session: Session = Depends(get_session)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    average_rating = None
    if user.role == UserRole.TEACHER:
        statement = select(func.avg(ProjectRating.rating)).join(Project).where(Project.teacher_id == user.id)
        result = session.exec(statement).first()
        if result:
            average_rating = round(result, 1)

    return UserProfile(
        id=user.id,
        full_name=user.full_name,
        bio=user.bio,
        languages=user.languages,
        role=user.role,
        created_at=user.created_at.isoformat(),
        average_rating=average_rating,
        intro_video_url=user.intro_video_url,
        sample_video_url=user.sample_video_url,
        avatar_url=user.avatar_url
    )

@router.get("/teachers", response_model=List[TeacherRead])
def search_teachers(
    query: str = Query(..., min_length=1),
    session: Session = Depends(get_session)
):
    statement = select(User).where(User.role == UserRole.TEACHER).where(User.full_name.ilike(f"%{query}%"))
    teachers = session.exec(statement).all()
    return [TeacherRead(id=t.id, full_name=t.full_name) for t in teachers]

@router.post("/stripe-onboarding-link", response_model=OnboardingResponse)
def create_stripe_onboarding_link(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can create Stripe onboarding links.")
    
    try:
        if not current_user.stripe_account_id:
            account = stripe.Account.create(type='express', email=current_user.email)
            current_user.stripe_account_id = account.id
            session.add(current_user)
            session.commit()
            session.refresh(current_user)
        
        account_link = stripe.AccountLink.create(
            account=current_user.stripe_account_id,
            refresh_url=f"{FRONTEND_URL}/settings?stripe_reauth=true",
            return_url=f"{FRONTEND_URL}/teacher/dashboard?stripe_return=true",
            type="account_onboarding",
        )
        
        return {"onboarding_url": account_link.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
