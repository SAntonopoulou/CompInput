from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import Video, Project, ProjectStatus, User, UserRole, Notification, Pledge, PledgeStatus

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

@router.post("/", response_model=Video)
def create_video(
    video_in: VideoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Submit a video for a funded project.
    """
    # Load project with pledges to notify backers
    project = session.exec(
        select(Project)
        .where(Project.id == video_in.project_id)
        .options(selectinload(Project.pledges))
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
    # We only notify backers who have successfully paid (CAPTURED)
    notified_users = set()
    for pledge in project.pledges:
        if pledge.status == PledgeStatus.CAPTURED and pledge.user_id not in notified_users:
            notification = Notification(
                user_id=pledge.user_id,
                content=f"New video posted in '{project.title}': {video.title}",
                is_read=False
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
