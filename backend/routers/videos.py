from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import Video, Project, ProjectStatus, User, UserRole, Notification, Pledge, PledgeStatus, VideoComment, VideoRating

router = APIRouter(prefix="/videos", tags=["videos"])

class VideoCreate(BaseModel):
    project_id: int
    title: str
    url: str
    platform: str = "youtube"
    duration: Optional[int] = None

class VideoRead(BaseModel):
    id: int
    title: str
    url: str
    platform: str
    duration: Optional[int]
    created_at: datetime
    project_id: int
    project_title: str
    teacher_name: str

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    content: str

class CommentRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
    user_name: str

    class Config:
        from_attributes = True

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

@router.post("/", response_model=Video)
def create_video(
    video_in: VideoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Submit a video for a funded project.
    """
    # Load project without pledges (optimization)
    # We only need basic project info here to verify ownership and status
    project = session.exec(
        select(Project)
        .where(Project.id == video_in.project_id)
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify user is the teacher
    if project.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can submit videos",
        )
    
    # Verify project status
    if project.status not in [ProjectStatus.FUNDED, ProjectStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail="Project must be FUNDED or IN_PROGRESS to submit videos",
        )
    
    # Create Video
    video = Video(
        title=video_in.title,
        url=video_in.url,
        platform=video_in.platform,
        duration=video_in.duration,
        project_id=project.id
    )
    session.add(video)
    
    # Update Project Status if needed
    if project.status == ProjectStatus.FUNDED:
        project.status = ProjectStatus.IN_PROGRESS
        session.add(project)
    
    # NOTIFICATION: Notify Backers
    # Optimization: Fetch only CAPTURED pledges directly from DB instead of loading all pledges
    statement = select(Pledge).where(
        Pledge.project_id == project.id,
        Pledge.status == PledgeStatus.CAPTURED
    )
    captured_pledges = session.exec(statement).all()

    notified_users = set()
    for pledge in captured_pledges:
        if pledge.user_id not in notified_users:
            notification = Notification(
                user_id=pledge.user_id,
                content=f"New video posted in '{project.title}': {video.title}",
                is_read=False,
                link=f"/projects/{project.id}"
            )
            session.add(notification)
            notified_users.add(pledge.user_id)
        
    session.commit()
    session.refresh(video)
    return video

@router.get("/", response_model=List[VideoRead])
def list_videos(
    limit: int = 10,
    offset: int = 0,
    language: Optional[str] = None,
    level: Optional[str] = None,
    teacher_id: Optional[int] = None,
    project_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Public archive of videos.
    """
    # Join Video -> Project to filter and check privacy
    query = select(Video).join(Project).where(Project.is_private == False)
    
    if language:
        query = query.where(Project.language == language)
    if level:
        query = query.where(Project.level == level)
    if teacher_id:
        query = query.where(Project.teacher_id == teacher_id)
    if project_id:
        query = query.where(Video.project_id == project_id)
        
    # Eager load project and teacher to avoid N+1
    query = query.options(selectinload(Video.project).selectinload(Project.teacher))
    
    query = query.offset(offset).limit(limit)
    
    videos = session.exec(query).all()
    
    results = []
    for v in videos:
        # Handle potential missing relationships gracefully, though they should exist
        project_title = v.project.title if v.project else "Unknown"
        teacher_name = v.project.teacher.full_name if (v.project and v.project.teacher) else "Unknown"
        
        results.append(VideoRead(
            id=v.id,
            title=v.title,
            url=v.url,
            platform=v.platform,
            duration=v.duration,
            created_at=v.created_at,
            project_id=v.project_id,
            project_title=project_title,
            teacher_name=teacher_name
        ))
        
    return results

@router.post("/{video_id}/comments", response_model=CommentRead)
def add_comment(
    video_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Add a comment to a video.
    """
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    comment = VideoComment(
        content=comment_in.content,
        user_id=current_user.id,
        video_id=video_id
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    
    return CommentRead(
        id=comment.id,
        content=comment.content,
        created_at=comment.created_at,
        user_id=comment.user_id,
        user_name=current_user.full_name
    )

@router.get("/{video_id}/comments", response_model=List[CommentRead])
def list_comments(
    video_id: int,
    session: Session = Depends(get_session)
):
    """
    List comments for a video.
    """
    statement = select(VideoComment).where(VideoComment.video_id == video_id).options(selectinload(VideoComment.user)).order_by(VideoComment.created_at.asc())
    comments = session.exec(statement).all()
    
    results = []
    for c in comments:
        user_name = c.user.full_name if c.user else "Unknown"
        results.append(CommentRead(
            id=c.id,
            content=c.content,
            created_at=c.created_at,
            user_id=c.user_id,
            user_name=user_name
        ))
    return results

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
    statement = select(VideoRating).where(VideoRating.video_id == video_id).options(selectinload(VideoRating.user)).order_by(VideoRating.created_at.desc())
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
