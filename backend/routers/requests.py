from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import Request, Project, ProjectStatus, User, UserRole, RequestStatus, Notification

router = APIRouter(prefix="/requests", tags=["requests"])

class RequestCreate(BaseModel):
    title: str
    description: str
    language: str
    level: str
    budget: int = 0 # in cents
    target_teacher_id: Optional[int] = None

class RequestRead(BaseModel):
    id: int
    title: str
    description: str
    language: str
    level: str
    budget: int
    status: RequestStatus
    target_teacher_id: Optional[int]
    counter_offer_amount: Optional[int]
    created_at: datetime
    user_id: int
    user_name: str

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    language: str
    level: str
    goal_amount: int
    status: ProjectStatus
    teacher_id: int
    origin_request_id: Optional[int] = None

    class Config:
        from_attributes = True

class CounterOffer(BaseModel):
    amount: int

@router.post("/", response_model=Request)
def create_request(
    request_in: RequestCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new content request.
    """
    request = Request(
        **request_in.dict(),
        user_id=current_user.id,
        status=RequestStatus.OPEN
    )
    session.add(request)
    session.commit()
    session.refresh(request)

    # Notify target teacher if specified
    if request.target_teacher_id:
        notification = Notification(
            user_id=request.target_teacher_id,
            content=f"Student {current_user.full_name} requested a video from you: {request.title}",
            is_read=False
        )
        session.add(notification)
        session.commit()

    return request

@router.get("/", response_model=List[RequestRead])
def list_requests(
    limit: int = 10,
    offset: int = 0,
    language: Optional[str] = None,
    level: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    List content requests.
    """
    query = select(Request).options(selectinload(Request.user))
    
    if language:
        query = query.where(Request.language == language)
    if level:
        query = query.where(Request.level == level)
        
    query = query.offset(offset).limit(limit)
    
    requests = session.exec(query).all()
    
    results = []
    for r in requests:
        user_name = r.user.full_name if r.user else "Unknown"
        results.append(RequestRead(
            id=r.id,
            title=r.title,
            description=r.description,
            language=r.language,
            level=r.level,
            budget=r.budget,
            status=r.status,
            target_teacher_id=r.target_teacher_id,
            counter_offer_amount=r.counter_offer_amount,
            created_at=r.created_at,
            user_id=r.user_id,
            user_name=user_name
        ))
        
    return results

@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete a request. Only the owner or an admin can delete it.
    """
    request = session.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if request.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this request",
        )
        
    session.delete(request)
    session.commit()
    return {"ok": True}

@router.post("/{request_id}/convert", response_model=ProjectResponse)
def convert_request_to_project(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Convert a request into a draft project (Accept Budget). Only teachers can do this.
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can convert requests to projects",
        )
        
    request = session.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Create Project from Request
    project = Project(
        title=request.title,
        description=request.description,
        language=request.language,
        level=request.level,
        goal_amount=request.budget, # Use the student's budget
        status=ProjectStatus.DRAFT,
        teacher_id=current_user.id,
        origin_request_id=request.id
    )
    
    request.status = RequestStatus.ACCEPTED
    session.add(request)
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Notify Student
    notification = Notification(
        user_id=request.user_id,
        content=f"Teacher {current_user.full_name} accepted your request '{request.title}'!",
        is_read=False
    )
    session.add(notification)
    session.commit()
    
    return project

@router.post("/{request_id}/counter", response_model=Request)
def counter_offer(
    request_id: int,
    offer: CounterOffer,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Teacher proposes a new price.
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Only teachers can make counter offers")
        
    request = session.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    request.counter_offer_amount = offer.amount
    request.status = RequestStatus.NEGOTIATING
    
    # If no target teacher was set, the countering teacher claims it
    if not request.target_teacher_id:
        request.target_teacher_id = current_user.id
        
    session.add(request)
    session.commit()
    session.refresh(request)
    
    # Notify Student
    notification = Notification(
        user_id=request.user_id,
        content=f"Teacher {current_user.full_name} proposed a new price for your request: {request.title}",
        is_read=False
    )
    session.add(notification)
    session.commit()
    
    return request

@router.post("/{request_id}/accept-offer", response_model=ProjectResponse)
def accept_offer(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Student accepts the teacher's counter offer.
    """
    request = session.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if not request.counter_offer_amount:
        raise HTTPException(status_code=400, detail="No counter offer to accept")
        
    if not request.target_teacher_id:
         raise HTTPException(status_code=400, detail="Teacher not identified for this offer")

    project = Project(
        title=request.title,
        description=request.description,
        language=request.language,
        level=request.level,
        goal_amount=request.counter_offer_amount,
        status=ProjectStatus.ACTIVE, # Ready for funding immediately
        teacher_id=request.target_teacher_id,
        origin_request_id=request.id
    )
    
    request.status = RequestStatus.ACCEPTED
    session.add(request)
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # Notify Teacher
    notification = Notification(
        user_id=request.target_teacher_id,
        content=f"Offer accepted! Project '{project.title}' is now created.",
        is_read=False
    )
    session.add(notification)
    session.commit()
    
    return project

@router.post("/{request_id}/reject-offer", response_model=Request)
def reject_offer(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Student rejects the offer.
    """
    request = session.get(Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    request.status = RequestStatus.REJECTED
    session.add(request)
    session.commit()
    session.refresh(request)
    
    if request.target_teacher_id:
        notification = Notification(
            user_id=request.target_teacher_id,
            content=f"Offer rejected for '{request.title}'.",
            is_read=False
        )
        session.add(notification)
        session.commit()
        
    return request
