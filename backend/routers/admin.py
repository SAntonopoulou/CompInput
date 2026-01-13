from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from ..database import get_session
from ..deps import get_current_admin
from ..models import User, Project, Pledge, UserRole, ProjectStatus, PledgeStatus, Request, Notification
from .projects import cancel_project

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
def get_stats(
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """
    Get system-wide statistics.
    """
    user_count = session.exec(select(func.count(User.id))).one()
    project_count = session.exec(select(func.count(Project.id))).one()
    pledge_count = session.exec(select(func.count(Pledge.id))).one()
    
    # Calculate total funds raised (captured pledges)
    total_funds_cents = session.exec(
        select(func.sum(Pledge.amount)).where(Pledge.status == PledgeStatus.CAPTURED)
    ).one() or 0
    
    return {
        "user_count": user_count,
        "project_count": project_count,
        "pledge_count": pledge_count,
        "total_funds_raised": total_funds_cents
    }

@router.get("/users", response_model=List[User])
def list_users(
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """
    List all users.
    """
    users = session.exec(select(User)).all()
    return users

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """
    Safely delete a user account (Admin override).
    """
    user_to_delete = session.get(User, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent deleting self
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    # 1. Find or Create "Deleted User"
    statement = select(User).where(User.email == "deleted@system")
    deleted_user = session.exec(statement).first()
    
    if not deleted_user:
        deleted_user = User(
            email="deleted@system",
            hashed_password="deleted",
            full_name="Deleted User",
            role=UserRole.STUDENT,
            bio="This user has deleted their account."
        )
        session.add(deleted_user)
        session.commit()
        session.refresh(deleted_user)
    
    # 2. Reassign Projects (Teacher)
    statement = select(Project).where(Project.teacher_id == user_to_delete.id)
    projects = session.exec(statement).all()
    for project in projects:
        project.teacher_id = deleted_user.id
        session.add(project)
        
    # 3. Reassign Pledges (Student)
    statement = select(Pledge).where(Pledge.user_id == user_to_delete.id)
    pledges = session.exec(statement).all()
    for pledge in pledges:
        pledge.user_id = deleted_user.id
        session.add(pledge)
        
    # 4. Reassign Requests (Student)
    statement = select(Request).where(Request.user_id == user_to_delete.id)
    requests = session.exec(statement).all()
    for request in requests:
        request.user_id = deleted_user.id
        session.add(request)

    # 5. Delete User
    session.delete(user_to_delete)
    session.commit()
    return

@router.delete("/projects/{project_id}")
def admin_cancel_project(
    project_id: int,
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """
    Cancel a project (Admin override).
    """
    # Reuse the existing cancel logic which handles refunds and notifications
    # The cancel_project function checks for admin role internally
    return cancel_project(project_id=project_id, current_user=current_user, session=session)
