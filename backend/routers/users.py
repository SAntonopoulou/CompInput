import stripe
import os
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import User, UserRole, Project, Pledge, Request, ProjectStatus, ProjectRating
from ..security import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

router = APIRouter(prefix="/users", tags=["users"])

# Pydantic Models
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

class ProjectInfoForRating(BaseModel):
    id: int
    title: str
    funding_goal: int
    language: str
    level: str
    tags: Optional[str] = None

class TeacherRatingRead(BaseModel):
    rating: int
    comment: Optional[str]
    created_at: datetime
    project: ProjectInfoForRating
    teacher_response: Optional[str] = None
    response_created_at: Optional[datetime] = None

# API Endpoints
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
        deleted_user = User(email="deleted@system", hashed_password="deleted", full_name="Deleted User", role=UserRole.STUDENT)
        session.add(deleted_user)
        session.commit()
        session.refresh(deleted_user)
    
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

@router.get("/{user_id}/ratings", response_model=List[TeacherRatingRead])
def get_teacher_ratings(
    user_id: int,
    session: Session = Depends(get_session)
):
    teacher = session.get(User, user_id)
    if not teacher or teacher.role != UserRole.TEACHER:
        raise HTTPException(status_code=404, detail="Teacher not found")

    statement = (
        select(ProjectRating)
        .join(Project)
        .where(Project.teacher_id == user_id)
        .options(selectinload(ProjectRating.project))
        .order_by(ProjectRating.created_at.desc())
    )
    
    ratings = session.exec(statement).all()
    
    return [
        TeacherRatingRead(
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
            project=ProjectInfoForRating(
                id=r.project.id,
                title=r.project.title,
                funding_goal=r.project.funding_goal,
                language=r.project.language,
                level=r.project.level,
                tags=r.project.tags
            ),
            teacher_response=r.teacher_response,
            response_created_at=r.response_created_at
        ) for r in ratings
    ]

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
