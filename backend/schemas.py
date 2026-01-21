from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Session, select

from .models import Project, Pledge, PledgeStatus, ProjectRating, Video, User, TeacherVerification, VerificationStatus

class MyRatingRead(BaseModel):
    rating: int
    comment: Optional[str]

class VideoReadSimple(BaseModel):
    id: int
    url: str

class LanguageLevelsRead(BaseModel):
    language: str
    levels: List[str]

class FilterOptionsRead(BaseModel):
    languages: List[LanguageLevelsRead]

class ProjectRead(BaseModel):
    id: int
    title: str
    description: str
    language: str
    level: str
    funding_goal: int
    current_funding: int
    tags: Optional[str] = None
    deadline: Optional[datetime]
    delivery_days: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    teacher_id: int
    teacher_name: str
    stripe_transfer_id: Optional[str] = None
    requester_name: Optional[str] = None
    requester_id: Optional[int] = None
    teacher_avatar_url: Optional[str] = None
    requester_avatar_url: Optional[str] = None
    origin_request_id: Optional[int] = None
    is_backer: bool = False
    my_rating: Optional[MyRatingRead] = None
    videos: List[VideoReadSimple] = []
    teacher_verified_languages: List[str] = []

    class Config:
        from_attributes = True

class PaginatedProjectRead(BaseModel):
    projects: List[ProjectRead]
    total_count: int

def _create_project_read(p: Project, current_user: Optional[User], session: Session) -> ProjectRead:
    teacher_name = p.teacher.full_name if p.teacher else "Unknown"
    requester_name = p.request.user.full_name if (p.request and p.request.user) else None
    requester_id = p.request.user.id if (p.request and p.request.user) else None
    teacher_avatar_url = p.teacher.avatar_url if p.teacher else None
    requester_avatar_url = p.request.user.avatar_url if (p.request and p.request.user) else None
    
    is_backer = False
    my_rating_obj = None
    if current_user:
        is_backer_pledge = session.exec(select(Pledge).where(Pledge.project_id == p.id, Pledge.user_id == current_user.id, Pledge.status == PledgeStatus.CAPTURED)).first()
        is_backer = is_backer_pledge is not None
        
        if is_backer:
            rating = session.exec(select(ProjectRating).where(ProjectRating.project_id == p.id, ProjectRating.user_id == current_user.id)).first()
            if rating:
                my_rating_obj = MyRatingRead(rating=rating.rating, comment=rating.comment)

    teacher_verified_languages = []
    if p.teacher:
        verifications = session.exec(select(TeacherVerification.language).where(
            TeacherVerification.teacher_id == p.teacher_id,
            TeacherVerification.status == VerificationStatus.APPROVED
        )).all()
        teacher_verified_languages = verifications

    return ProjectRead(
        id=p.id,
        title=p.title,
        description=p.description,
        language=p.language,
        level=p.level,
        funding_goal=p.funding_goal,
        tags=p.tags,
        current_funding=p.current_funding,
        deadline=p.deadline,
        delivery_days=p.delivery_days,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
        teacher_id=p.teacher_id,
        teacher_name=teacher_name,
        stripe_transfer_id=p.stripe_transfer_id,
        requester_name=requester_name,
        requester_id=requester_id,
        teacher_avatar_url=teacher_avatar_url,
        requester_avatar_url=requester_avatar_url,
        origin_request_id=p.origin_request_id,
        is_backer=is_backer,
        my_rating=my_rating_obj,
        videos=[VideoReadSimple(id=v.id, url=v.url) for v in p.videos],
        teacher_verified_languages=teacher_verified_languages
    )
