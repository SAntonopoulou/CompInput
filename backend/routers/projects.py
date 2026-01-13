from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from ..database import get_session
from ..deps import get_current_user
from ..models import Project, ProjectStatus, User, UserRole
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])

# Pydantic models for request/response
class ProjectCreate(BaseModel):
    title: str
    description: str
    language: str
    level: str
    goal_amount: int
    deadline: Optional[datetime] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    level: Optional[str] = None
    goal_amount: Optional[int] = None
    deadline: Optional[datetime] = None
    status: Optional[ProjectStatus] = None

class ProjectRead(BaseModel):
    id: int
    title: str
    description: str
    language: str
    level: str
    goal_amount: int
    current_amount: int
    deadline: Optional[datetime]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    teacher_id: int
    teacher_name: str

    class Config:
        orm_mode = True

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
        status=ProjectStatus.DRAFT
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.get("/", response_model=List[ProjectRead])
def list_projects(
    language: Optional[str] = None,
    level: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    List public projects.
    """
    query = select(Project).where(
        (Project.status == ProjectStatus.ACTIVE) | 
        (Project.status == ProjectStatus.FUNDED)
    ).options(selectinload(Project.teacher))
    
    if language:
        query = query.where(Project.language == language)
    if level:
        query = query.where(Project.level == level)
        
    projects = session.exec(query).all()
    
    # Transform to ProjectRead to include teacher name
    # Note: In a larger app, we might want to use a join in the query
    result = []
    for p in projects:
        # Ensure teacher is loaded (lazy loading might happen here)
        teacher_name = p.teacher.full_name if p.teacher else "Unknown"
        
        project_read = ProjectRead(
            id=p.id,
            title=p.title,
            description=p.description,
            language=p.language,
            level=p.level,
            goal_amount=p.goal_amount,
            current_amount=p.current_amount,
            deadline=p.deadline,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
            teacher_id=p.teacher_id,
            teacher_name=teacher_name
        )
        result.append(project_read)
        
    return result

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    session: Session = Depends(get_session)
):
    """
    Get project details.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    teacher_name = project.teacher.full_name if project.teacher else "Unknown"
    
    return ProjectRead(
        id=project.id,
        title=project.title,
        description=project.description,
        language=project.language,
        level=project.level,
        goal_amount=project.goal_amount,
        current_amount=project.current_amount,
        deadline=project.deadline,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        teacher_id=project.teacher_id,
        teacher_name=teacher_name
    )

@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
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
    for key, value in project_data.items():
        setattr(project, key, value)
        
    project.updated_at = datetime.utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project
