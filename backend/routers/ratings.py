from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import ProjectRating, User, Pledge, PledgeStatus, Project, ProjectStatus

router = APIRouter(prefix="/projects", tags=["ratings"])

class RatingCreate(BaseModel):
    rating: int
    comment: Optional[str] = None

class RatingRead(BaseModel):
    id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
    user_id: int
    user_name: str

    class Config:
        from_attributes = True

@router.post("/{project_id}/rate", response_model=ProjectRating)
def rate_project(
    project_id: int,
    rating_in: RatingCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Rate a project. A user can only rate a project once.
    """
    if not (1 <= rating_in.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed projects can be rated.")

    # Verify the user is a backer of this project
    pledge = session.exec(
        select(Pledge).where(
            Pledge.project_id == project_id,
            Pledge.user_id == current_user.id,
            Pledge.status == PledgeStatus.CAPTURED
        )
    ).first()
    if not pledge:
        raise HTTPException(status_code=403, detail="You must be a backer to rate this project.")

    # Verify the user has not already rated this project
    existing_rating = session.exec(
        select(ProjectRating).where(
            ProjectRating.project_id == project_id,
            ProjectRating.user_id == current_user.id
        )
    ).first()
    if existing_rating:
        raise HTTPException(status_code=400, detail="You have already rated this project.")

    # Create the new rating
    rating = ProjectRating(
        project_id=project_id,
        user_id=current_user.id,
        rating=rating_in.rating,
        comment=rating_in.comment
    )
    session.add(rating)
    session.commit()
    session.refresh(rating)
    return rating

@router.get("/{project_id}/ratings", response_model=List[RatingRead])
def list_project_ratings(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    List all ratings for a specific project.
    """
    statement = select(ProjectRating).where(ProjectRating.project_id == project_id).order_by(ProjectRating.created_at.desc())
    ratings = session.exec(statement).all()
    
    results = []
    for r in ratings:
        user_name = r.user.full_name if r.user else "Unknown"
        results.append(RatingRead(
            id=r.id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
            user_id=r.user_id,
            user_name=user_name
        ))
    return results
