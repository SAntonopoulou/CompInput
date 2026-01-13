from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import VideoRating, Video, User, Pledge, PledgeStatus, Project

router = APIRouter(prefix="/videos", tags=["ratings"])

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

@router.post("/{video_id}/rate", response_model=VideoRating)
def rate_video(
    video_id: int,
    rating_in: RatingCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Rate a video.
    """
    if rating_in.rating < 1 or rating_in.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if user has already rated this video
    statement = select(VideoRating).where(
        VideoRating.video_id == video_id,
        VideoRating.user_id == current_user.id
    )
    existing_rating = session.exec(statement).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_in.rating
        existing_rating.comment = rating_in.comment
        existing_rating.created_at = datetime.utcnow()
        session.add(existing_rating)
        session.commit()
        session.refresh(existing_rating)
        return existing_rating
    
    # Create new rating
    rating = VideoRating(
        video_id=video_id,
        user_id=current_user.id,
        rating=rating_in.rating,
        comment=rating_in.comment
    )
    session.add(rating)
    session.commit()
    session.refresh(rating)
    return rating

@router.get("/{video_id}/ratings", response_model=List[RatingRead])
def list_video_ratings(
    video_id: int,
    session: Session = Depends(get_session)
):
    """
    List ratings for a video.
    """
    statement = select(VideoRating).where(VideoRating.video_id == video_id).order_by(VideoRating.created_at.desc())
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
