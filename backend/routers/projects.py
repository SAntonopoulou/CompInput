import stripe
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from ..database import get_session
from ..deps import get_current_user
from ..models import Project, ProjectStatus, User, UserRole, PledgeStatus, Notification, Request, RequestStatus, ProjectUpdate
from ..security import STRIPE_SECRET_KEY
from pydantic import BaseModel

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/projects", tags=["projects"])

# Pydantic models for request/response
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

@router.post("/", response_model=Project)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new project. Only teachers can create projects.
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create projects",
        )
    
    project = Project(
        **project_in.dict(),
        teacher_id=current_user.id,
        status=ProjectStatus.FUNDING
    )
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
    """
    List public projects.
    """
    query = select(Project).where(
        (Project.status == ProjectStatus.FUNDING) | 
        (Project.status == ProjectStatus.SUCCESSFUL)
    ).where(
        (Project.is_private == False)
    ).options(
        selectinload(Project.teacher),
        selectinload(Project.request).selectinload(Request.user)
    )
    
    if language:
        query = query.where(Project.language == language)
    if level:
        query = query.where(Project.level == level)
    if tag:
        query = query.where(Project.tags.contains(tag))
    if search:
        query = query.where(or_(
            Project.title.ilike(f"%{search}%"),
            Project.description.ilike(f"%{search}%")
        ))
    
    query = query.offset(offset).limit(limit)
        
    projects = session.exec(query).all()
    
    result = []
    for p in projects:
        teacher_name = p.teacher.full_name if p.teacher else "Unknown"
        requester_name = p.request.user.full_name if (p.request and p.request.user) else None
        requester_id = p.request.user.id if (p.request and p.request.user) else None
        teacher_avatar_url = p.teacher.avatar_url if p.teacher else None
        requester_avatar_url = p.request.user.avatar_url if (p.request and p.request.user) else None
        
        project_read = ProjectRead(
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
            origin_request_id=p.origin_request_id
        )
        result.append(project_read)
        
    return result

@router.get("/me", response_model=List[ProjectRead])
def list_my_projects(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    List projects owned by the current teacher (including drafts).
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can list their projects",
        )
    
    query = select(Project).where(Project.teacher_id == current_user.id).options(
        selectinload(Project.teacher),
        selectinload(Project.request).selectinload(Request.user)
    )
    projects = session.exec(query).all()
    
    result = []
    for p in projects:
        teacher_name = p.teacher.full_name if p.teacher else "Unknown"
        requester_name = p.request.user.full_name if (p.request and p.request.user) else None
        requester_id = p.request.user.id if (p.request and p.request.user) else None
        teacher_avatar_url = p.teacher.avatar_url if p.teacher else None
        requester_avatar_url = p.request.user.avatar_url if (p.request and p.request.user) else None
        
        project_read = ProjectRead(
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
            origin_request_id=p.origin_request_id
        )
        result.append(project_read)
        
    return result

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get project details.
    """
    project = session.exec(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.teacher), selectinload(Project.request).selectinload(Request.user))
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    teacher_name = project.teacher.full_name if project.teacher else "Unknown"
    requester_name = project.request.user.full_name if (project.request and project.request.user) else None
    requester_id = project.request.user.id if (project.request and project.request.user) else None
    teacher_avatar_url = project.teacher.avatar_url if project.teacher else None
    requester_avatar_url = project.request.user.avatar_url if (project.request and project.request.user) else None
    
    return ProjectRead(
        id=project.id,
        title=project.title,
        description=project.description,
        language=project.language,
        level=project.level,
        funding_goal=project.funding_goal,
        tags=project.tags,
        current_funding=project.current_funding,
        deadline=project.deadline,
        delivery_days=project.delivery_days,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        teacher_id=project.teacher_id,
        teacher_name=teacher_name,
        stripe_transfer_id=project.stripe_transfer_id,
        requester_name=requester_name,
        requester_id=requester_id,
        teacher_avatar_url=teacher_avatar_url,
        requester_avatar_url=requester_avatar_url,
        origin_request_id=project.origin_request_id
    )

@router.get("/{project_id}/related", response_model=List[ProjectRead])
def get_related_projects(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Get related projects based on language and level/tags.
    """
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
    ).limit(10) 

    candidates = session.exec(query).all()
    
    scored_candidates = []
    project_tags = set(project.tags.split(',')) if project.tags else set()
    
    for p in candidates:
        score = 0
        if p.level == project.level:
            score += 2
        
        p_tags = set(p.tags.split(',')) if p.tags else set()
        if project_tags and p_tags:
            overlap = project_tags.intersection(p_tags)
            score += len(overlap)
            
        scored_candidates.append((score, p))
    
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    
    results = []
    for _, p in scored_candidates[:3]:
        teacher_name = p.teacher.full_name if p.teacher else "Unknown"
        requester_name = p.request.user.full_name if (p.request and p.request.user) else None
        requester_id = p.request.user.id if (p.request and p.request.user) else None
        teacher_avatar_url = p.teacher.avatar_url if p.teacher else None
        requester_avatar_url = p.request.user.avatar_url if (p.request and p.request.user) else None

        results.append(ProjectRead(
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
            origin_request_id=p.origin_request_id
        ))
        
    return results

@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_in: ProjectUpdateModel,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update a project. Only the owner can update it.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project",
        )
        
    project_data = project_in.dict(exclude_unset=True)
    
    if "funding_goal" in project_data:
        if project_data["funding_goal"] != project.funding_goal:
            if project.status != ProjectStatus.DRAFT or project.origin_request_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change the price of an active project or one created from a request",
                )
            
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
    """
    Mark a project as completed and trigger payout.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can complete the project",
        )
        
    if project.status != ProjectStatus.SUCCESSFUL:
        raise HTTPException(
            status_code=400,
            detail="Project must be SUCCESSFUL to be completed",
        )

    if project.stripe_transfer_id:
        raise HTTPException(
            status_code=400,
            detail="This project has already been paid out.",
        )
    
    teacher = project.teacher
    if not teacher.stripe_account_id:
        raise HTTPException(
            status_code=400,
            detail="Teacher has not connected a Stripe account for payouts",
        )
        
    platform_fee_percent = 0.15
    amount_collected = project.current_funding
    platform_fee = int(amount_collected * platform_fee_percent)
    payout_amount = amount_collected - platform_fee
    
    if payout_amount > 0:
        try:
            transfer = stripe.Transfer.create(
                amount=payout_amount,
                currency="usd",
                destination=teacher.stripe_account_id,
                metadata={"project_id": str(project.id)},
            )
            project.stripe_transfer_id = transfer.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payout failed: {str(e)}")
    
    project.status = ProjectStatus.COMPLETED
    session.add(project)
    session.commit()
    session.refresh(project)
    
    return project

@router.post("/{project_id}/cancel", response_model=Project)
def cancel_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Cancel a project and refund backers.
    """
    project = session.exec(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.pledges))
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.teacher_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the project owner can cancel the project",
        )
        
    if project.status == ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a completed project",
        )
        
    for pledge in project.pledges:
        try:
            if pledge.status == PledgeStatus.CAPTURED:
                stripe.Refund.create(payment_intent=pledge.payment_intent_id)
                pledge.status = PledgeStatus.REFUNDED
                session.add(pledge)
                
                notification = Notification(
                    user_id=pledge.user_id,
                    content=f"Project '{project.title}' was cancelled and you have been refunded.",
                    is_read=False,
                    link="/"
                )
                session.add(notification)
                
            elif pledge.status == PledgeStatus.AUTHORIZED:
                stripe.PaymentIntent.cancel(pledge.payment_intent_id)
                pledge.status = PledgeStatus.REFUNDED
                session.add(pledge)
                
        except stripe.error.StripeError as e:
            print(f"Failed to refund pledge {pledge.id}: {str(e)}")
            
    project.status = ProjectStatus.CANCELLED
    session.add(project)
    
    if project.origin_request_id:
        request = session.get(Request, project.origin_request_id)
        if request:
            request.status = RequestStatus.OPEN
            request.target_teacher_id = None
            request.is_private = False
            session.add(request)
            
            notification = Notification(
                user_id=request.user_id,
                content=f"Project '{project.title}' was cancelled. Your request has been reopened for other teachers.",
                is_read=False,
                link="/requests"
            )
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
    """
    Add a status update to a project.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the project owner can post updates")
        
    update = ProjectUpdate(
        content=update_in.content,
        project_id=project_id
    )
    session.add(update)
    session.commit()
    session.refresh(update)
    
    return UpdateRead(
        id=update.id,
        content=update.content,
        created_at=update.created_at,
        project_id=update.project_id
    )

@router.get("/{project_id}/updates", response_model=List[UpdateRead])
def list_project_updates(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    List updates for a project.
    """
    statement = select(ProjectUpdate).where(ProjectUpdate.project_id == project_id).order_by(ProjectUpdate.created_at.desc())
    updates = session.exec(statement).all()
    return updates
