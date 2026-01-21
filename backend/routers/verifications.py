from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from ..database import get_session
from ..deps import get_current_user
from ..models import TeacherVerification, User, UserRole, VerificationStatus

router = APIRouter(prefix="/verifications", tags=["verifications"])

class VerificationCreate(BaseModel):
    language: str
    document_url: str

@router.post("/", response_model=TeacherVerification, status_code=status.HTTP_201_CREATED)
def submit_verification_request(
    verification_in: VerificationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Allows a teacher to submit a new language verification request.
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can submit verification requests.",
        )

    existing_request = session.exec(
        select(TeacherVerification).where(
            TeacherVerification.teacher_id == current_user.id,
            TeacherVerification.language == verification_in.language,
            TeacherVerification.status.in_([VerificationStatus.PENDING, VerificationStatus.APPROVED])
        )
    ).first()
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a pending or approved verification for {verification_in.language}.",
        )

    verification = TeacherVerification(
        teacher_id=current_user.id,
        language=verification_in.language,
        document_url=verification_in.document_url,
        status=VerificationStatus.PENDING,
    )
    session.add(verification)
    session.commit()
    session.refresh(verification)
    return verification

@router.get("/me", response_model=List[TeacherVerification])
def get_my_verifications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get all verification requests for the current teacher.
    """
    if current_user.role != UserRole.TEACHER:
        return []
        
    return current_user.verifications
