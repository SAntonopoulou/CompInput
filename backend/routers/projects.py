import stripe
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_
import os

import logging
from ..database import get_session
from ..deps import get_current_user
from ..models import Project, ProjectStatus, User, UserRole, PledgeStatus, Notification, Request, RequestStatus, ProjectUpdate, Pledge, ProjectRating
from ..security import STRIPE_SECRET_KEY
from pydantic import BaseModel

logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY
PLATFORM_FEE_PERCENT = float(os.getenv("PLATFORM_FEE_PERCENT", "0.15"))

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    title: str
    description: str
    language: str
    level: str
    funding_goal: int
    delivery_days: int
    tags: Optional[str] = None

class ProjectUpdateModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    funding_goal: Optional[int] = None
    deadline: Optional[datetime] = None
    delivery_days: Optional[int] = None
    status: Optional[ProjectStatus] = None
    tags: Optional[str] = None

class MyRatingRead(BaseModel):
    rating: int
    comment: Optional[str]

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
    status: ProjectStatus
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

    class Config:
        from_attributes = True

class UpdateCreate(BaseModel):
    content: str

class UpdateRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    project_id: int

    class Config:
        from_attributes = True

def _create_project_read(p: Project, current_user: User, session: Session) -> ProjectRead:
    teacher_name = p.teacher.full_name if p.teacher else "Unknown"
    requester_name = p.request.user.full_name if (p.request and p.request.user) else None
    requester_id = p.request.user.id if (p.request and p.request.user) else None
    teacher_avatar_url = p.teacher.avatar_url if p.teacher else None
    requester_avatar_url = p.request.user.avatar_url if (p.request and p.request.user) else None
    
    is_backer = False
    my_rating_obj = None
    if current_user:
        is_backer = session.exec(select(Pledge).where(Pledge.project_id == p.id, Pledge.user_id == current_user.id, Pledge.status == PledgeStatus.CAPTURED)).first() is not None
        
        if is_backer:
            rating = session.exec(select(ProjectRating).where(ProjectRating.project_id == p.id, ProjectRating.user_id == current_user.id)).first()
            if rating:
                my_rating_obj = MyRatingRead(rating=rating.rating, comment=rating.comment)

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
        my_rating=my_rating_obj
    )

@router.post("/", response_model=Project)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can create projects")
    
    project = Project(**project_in.dict(), teacher_id=current_user.id, status=ProjectStatus.FUNDING)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("/", response_model=List[ProjectRead])
def list_projects(
    language: Optional[str] = None,
    level: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 9,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    query = select(Project).where(
        (Project.status == ProjectStatus.FUNDING) | 
        (Project.status == ProjectStatus.SUCCESSFUL)
    ).where(
        (Project.is_private == False)
    ).options(
        selectinload(Project.teacher),
        selectinload(Project.request).selectinload(Request.user)
    )

    if language: query = query.where(Project.language == language)
    if level: query = query.where(Project.level == level)
    if tag: query = query.where(Project.tags.contains(tag))
    if search: query = query.where(or_(Project.title.ilike(f"%{search}%"), Project.description.ilike(f"%{search}%")))

    projects = session.exec(query.offset(offset).limit(limit)).all()
    return [_create_project_read(p, current_user, session) for p in projects]

@router.get("/me", response_model=List[ProjectRead])
def list_my_projects(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can list their projects")
    
    query = select(Project).where(Project.teacher_id == current_user.id).options(
        selectinload(Project.teacher),
        selectinload(Project.request).selectinload(Request.user)
    )
    projects = session.exec(query).all()
    return [_create_project_read(p, current_user, session) for p in projects]

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    project = session.exec(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.teacher), selectinload(Project.request).selectinload(Request.user))
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.teacher_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if project.status in [ProjectStatus.DRAFT, ProjectStatus.ON_HOLD] and not (is_owner or is_admin):
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status == ProjectStatus.CANCELLED and not is_admin:
        raise HTTPException(status_code=404, detail="Project not found")
            
    return _create_project_read(project, current_user, session)

@router.get("/{project_id}/related", response_model=List[ProjectRead])
def get_related_projects(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = select(Project).where(
        Project.language == project.language,
        Project.id != project_id,
        (Project.status == ProjectStatus.FUNDING) | (Project.status == ProjectStatus.SUCCESSFUL),
        Project.is_private == False
    ).options(
        selectinload(Project.teacher),
        selectinload(Project.request).selectinload(Request.user)
    ).limit(3)
    
    projects = session.exec(query).all()
    return [_create_project_read(p, current_user, session) for p in projects]

@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_in: ProjectUpdateModel,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this project")

    project_data = project_in.dict(exclude_unset=True)
    if "funding_goal" in project_data and project_data["funding_goal"] != project.funding_goal:
        if project.status != ProjectStatus.DRAFT or project.origin_request_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change the price of an active project or one created from a request")

    for key, value in project_data.items():
        setattr(project, key, value)

    project.updated_at = datetime.utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.post("/{project_id}/complete", response_model=Project)
def complete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can complete the project")
    if project.status != ProjectStatus.SUCCESSFUL:
        raise HTTPException(status_code=400, detail="Project must be SUCCESSFUL to be marked for completion")

    project.status = ProjectStatus.PENDING_CONFIRMATION
    session.add(project)

    backers = session.exec(select(User).join(Pledge).where(Pledge.project_id == project_id, Pledge.status == PledgeStatus.CAPTURED)).all()
    for backer in backers:
        notification = Notification(
            user_id=backer.id,
            content=f"Project '{project.title}' is ready for your review. Please confirm its completion.",
            link=f"/projects/{project.id}"
        )
        session.add(notification)

    session.commit()
    session.refresh(project)
    return project

@router.post("/{project_id}/confirm-completion", response_model=Project)
def confirm_completion(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status != ProjectStatus.PENDING_CONFIRMATION:
        raise HTTPException(status_code=400, detail="Project is not awaiting confirmation.")

    pledge = session.exec(select(Pledge).where(Pledge.project_id == project_id, Pledge.user_id == current_user.id, Pledge.status == PledgeStatus.CAPTURED)).first()
    if not pledge:
        raise HTTPException(status_code=403, detail="You are not a backer of this project.")

    if project.stripe_transfer_id:
        raise HTTPException(status_code=400, detail="This project has already been paid out.")

    teacher = session.get(User, project.teacher_id)
    if not teacher or not teacher.stripe_account_id:
        raise HTTPException(status_code=400, detail="Teacher has not connected a Stripe account for payouts.")

    amount_collected = project.current_funding
    platform_fee = int(amount_collected * PLATFORM_FEE_PERCENT)
    payout_amount = amount_collected - platform_fee

    if payout_amount > 0:
        try:
            transfer = stripe.Transfer.create(
                amount=payout_amount,
                currency="eur",
                destination=teacher.stripe_account_id,
                metadata={"project_id": str(project.id)},
            )
            project.stripe_transfer_id = transfer.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payout failed: {str(e)}")

    project.status = ProjectStatus.COMPLETED
    session.add(project)

    notification = Notification(
        user_id=project.teacher_id,
        content=f"Your funds for project '{project.title}' have been released.",
        link=f"/teacher/dashboard"
    )
    session.add(notification)

    session.commit()
    session.refresh(project)
    return project

@router.post("/{project_id}/cancel", response_model=Project)
def cancel_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    project = session.exec(select(Project).where(Project.id == project_id).options(selectinload(Project.pledges))).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can cancel the project")
    if project.status == ProjectStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed project")

    for pledge in project.pledges:
        if pledge.status == PledgeStatus.CAPTURED:
            try:
                stripe.Refund.create(payment_intent=pledge.payment_intent_id)
                pledge.status = PledgeStatus.REFUNDED
                session.add(pledge)
                notification = Notification(user_id=pledge.user_id, content=f"Project '{project.title}' was cancelled and you have been refunded.", link="/")
                session.add(notification)
            except stripe.error.StripeError as e:
                logger.error(f"Failed to refund pledge {pledge.id}: {e}")

    project.status = ProjectStatus.CANCELLED
    session.add(project)

    if project.origin_request_id:
        request = session.get(Request, project.origin_request_id)
        if request:
            request.status = RequestStatus.OPEN
            request.target_teacher_id = None
            request.is_private = False
            session.add(request)
            notification = Notification(user_id=request.user_id, content=f"Project '{project.title}' was cancelled. Your request has been reopened.", link="/requests")
            session.add(notification)

    session.commit()
    session.refresh(project)
    return project

@router.post("/{project_id}/updates", response_model=UpdateRead)
def add_project_update(
    project_id: int,
    update_in: UpdateCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the project owner can post updates")

    update = ProjectUpdate(content=update_in.content, project_id=project_id)
    session.add(update)
    session.commit()
    session.refresh(update)
    return update

@router.patch("/updates/{update_id}", response_model=UpdateRead)
def edit_project_update(
    update_id: int,
    update_in: UpdateCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    db_update = session.get(ProjectUpdate, update_id, options=[selectinload(ProjectUpdate.project)])
    if not db_update:
        raise HTTPException(status_code=404, detail="Update not found")
    if db_update.project.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this update")

    db_update.content = update_in.content
    session.add(db_update)
    session.commit()
    session.refresh(db_update)
    return db_update

@router.get("/{project_id}/updates", response_model=List[UpdateRead])
def list_project_updates(
    project_id: int,
    session: Session = Depends(get_session)
):
    statement = select(ProjectUpdate).where(ProjectUpdate.project_id == project_id).order_by(ProjectUpdate.created_at.desc())
    updates = session.exec(statement).all()
    return updates
