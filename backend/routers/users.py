import stripe
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, update, func
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import User, UserRole, Project, Pledge, Request, ProjectStatus, PledgeStatus, RequestStatus, Video, VideoRating
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

class UserProfile(BaseModel):
    id: int
    full_name: str
    bio: Optional[str]
    languages: Optional[str]
    role: UserRole
    created_at: str
    average_rating: Optional[float] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[str] = None

@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user details.
    """
    return current_user

@router.patch("/me", response_model=User)
def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update current user profile.
    """
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
    """
    Safely delete the current user account.
    Reassigns related data to a system 'Deleted User' account.
    """
    # 1. Find or Create "Deleted User"
    statement = select(User).where(User.email == "deleted@system")
    deleted_user = session.exec(statement).first()
    
    if not deleted_user:
        deleted_user = User(
            email="deleted@system",
            hashed_password="deleted",
            full_name="Deleted User",
            role=UserRole.STUDENT,
            bio="This user has deleted their account."
        )
        session.add(deleted_user)
        session.commit()
        session.refresh(deleted_user)
    
    # 2. Reassign Projects (Teacher)
    statement = select(Project).where(Project.teacher_id == current_user.id)
    projects = session.exec(statement).all()
    for project in projects:
        project.teacher_id = deleted_user.id
        session.add(project)
        
    # 3. Reassign Pledges (Student)
    statement = select(Pledge).where(Pledge.user_id == current_user.id)
    pledges = session.exec(statement).all()
    for pledge in pledges:
        pledge.user_id = deleted_user.id
        session.add(pledge)
        
    # 4. Reassign Requests (Student)
    statement = select(Request).where(Request.user_id == current_user.id)
    requests = session.exec(statement).all()
    for request in requests:
        request.user_id = deleted_user.id
        session.add(request)

    # 5. Delete User
    session.delete(current_user)
    session.commit()
    return

@router.get("/{user_id}/profile", response_model=UserProfile)
def get_user_profile(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Get public profile of a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    average_rating = None
    if user.role == UserRole.TEACHER:
        # Calculate average rating for teacher
        # Join Video -> VideoRating
        # Filter by Video.project.teacher_id == user.id
        # But Video doesn't have teacher_id directly, it's via Project
        # So: VideoRating -> Video -> Project -> Teacher
        
        statement = select(func.avg(VideoRating.rating)).join(Video).join(Project).where(Project.teacher_id == user.id)
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
        average_rating=average_rating
    )

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
