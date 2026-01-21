from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..database import get_session
from ..deps import get_current_user
from ..models import User, UserRole, Request, Conversation, ConversationStatus, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Pydantic Schemas
class ConversationCreate(BaseModel):
    request_id: int

class MessageCreate(BaseModel):
    content: str

class DemoVideoUpdate(BaseModel):
    url: str

class UserPublicRead(BaseModel):
    id: int
    full_name: str
    avatar_url: Optional[str] = None
    role: UserRole

    class Config:
        from_attributes = True

class MessageRead(BaseModel):
    id: int
    sender_id: int
    content: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class ConversationRead(BaseModel):
    id: int
    request_id: int
    teacher_id: int
    student_id: int
    status: ConversationStatus
    student_demo_video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    request_title: str # To be populated from Request
    teacher: UserPublicRead
    student: UserPublicRead
    messages: List[MessageRead] = [] # Only for full conversation view

    class Config:
        from_attributes = True

class ConversationSummaryRead(BaseModel):
    id: int
    request_id: int
    teacher_id: int
    student_id: int
    status: ConversationStatus
    updated_at: datetime
    
    request_title: str
    other_participant: UserPublicRead
    last_message_content: Optional[str] = None
    last_message_created_at: Optional[datetime] = None
    unread_messages_count: int = 0

    class Config:
        from_attributes = True

class InboxSummary(BaseModel):
    conversations: List[ConversationSummaryRead]
    total_unread_count: int

# Helper to create ConversationRead from Conversation model
def _create_conversation_read(conversation: Conversation, current_user: User, session: Session) -> ConversationRead:
    # Ensure relationships are loaded
    if not conversation.request:
        conversation.request = session.get(Request, conversation.request_id)
    if not conversation.teacher:
        conversation.teacher = session.get(User, conversation.teacher_id)
    if not conversation.student:
        conversation.student = session.get(User, conversation.student_id)

    return ConversationRead(
        id=conversation.id,
        request_id=conversation.request_id,
        teacher_id=conversation.teacher_id,
        student_id=conversation.student_id,
        status=conversation.status,
        student_demo_video_url=conversation.student_demo_video_url,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        request_title=conversation.request.title,
        teacher=UserPublicRead.model_validate(conversation.teacher),
        student=UserPublicRead.model_validate(conversation.student),
        messages=[MessageRead.model_validate(msg) for msg in conversation.messages]
    )

# Helper to create ConversationSummaryRead from Conversation model
def _create_conversation_summary_read(conversation: Conversation, current_user: User, session: Session) -> ConversationSummaryRead:
    # Ensure relationships are loaded
    if not conversation.request:
        conversation.request = session.get(Request, conversation.request_id)
    if not conversation.teacher:
        conversation.teacher = session.get(User, conversation.teacher_id)
    if not conversation.student:
        conversation.student = session.get(User, conversation.student_id)

    other_participant = conversation.teacher if conversation.student_id == current_user.id else conversation.student
    
    last_message = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
    ).first()

    unread_messages_count = session.exec(
        select(func.count(Message.id))
        .where(Message.conversation_id == conversation.id)
        .where(Message.sender_id != current_user.id)
        .where(Message.is_read == False)
    ).one()

    return ConversationSummaryRead(
        id=conversation.id,
        request_id=conversation.request_id,
        teacher_id=conversation.teacher_id,
        student_id=conversation.student_id,
        status=conversation.status,
        updated_at=conversation.updated_at,
        request_title=conversation.request.title,
        other_participant=UserPublicRead.model_validate(other_participant),
        last_message_content=last_message.content if last_message else None,
        last_message_created_at=last_message.created_at if last_message else None,
        unread_messages_count=unread_messages_count
    )


@router.post("/", response_model=ConversationRead)
def create_conversation(
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can initiate conversations.")

    request = session.get(Request, conversation_in.request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    if request.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create a conversation for your own request.")
    
    # Check if conversation already exists
    existing_conversation = session.exec(
        select(Conversation)
        .where(Conversation.request_id == conversation_in.request_id)
        .where(Conversation.teacher_id == current_user.id)
    ).first()

    if existing_conversation:
        return _create_conversation_read(existing_conversation, current_user, session)

    conversation = Conversation(
        request_id=request.id,
        teacher_id=current_user.id,
        student_id=request.user_id,
        status=ConversationStatus.OPEN,
        updated_at=datetime.utcnow()
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Add initial message from teacher
    initial_message_content = f"Hi, I'm interested in your request for '{request.title}'. Let's discuss!"
    initial_message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=initial_message_content,
        is_read=False
    )
    session.add(initial_message)
    session.commit()
    session.refresh(conversation) # Refresh to update updated_at

    return _create_conversation_read(conversation, current_user, session)

@router.get("/", response_model=List[ConversationSummaryRead])
def list_my_conversations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    conversations = session.exec(
        select(Conversation)
        .where(
            (Conversation.teacher_id == current_user.id) |
            (Conversation.student_id == current_user.id)
        )
        .options(
            selectinload(Conversation.request),
            selectinload(Conversation.teacher),
            selectinload(Conversation.student)
        )
        .order_by(Conversation.updated_at.desc())
    ).all()

    return [_create_conversation_summary_read(conv, current_user, session) for conv in conversations]

@router.get("/summary", response_model=InboxSummary)
def get_inbox_summary(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    conversations = session.exec(
        select(Conversation)
        .where(
            (Conversation.teacher_id == current_user.id) |
            (Conversation.student_id == current_user.id)
        )
        .options(
            selectinload(Conversation.request),
            selectinload(Conversation.teacher),
            selectinload(Conversation.student)
        )
        .order_by(Conversation.updated_at.desc())
    ).all()

    summary_conversations = []
    total_unread_count = 0
    for conv in conversations:
        summary_conv = _create_conversation_summary_read(conv, current_user, session)
        summary_conversations.append(summary_conv)
        total_unread_count += summary_conv.unread_messages_count
    
    return InboxSummary(conversations=summary_conversations, total_unread_count=total_unread_count)


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_full_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    conversation = session.exec(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.request),
            selectinload(Conversation.teacher),
            selectinload(Conversation.student),
            selectinload(Conversation.messages)
        )
    ).first()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    
    if not (conversation.teacher_id == current_user.id or conversation.student_id == current_user.id or current_user.role == UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this conversation.")

    # Mark messages from the other participant as read
    for message in conversation.messages:
        if message.sender_id != current_user.id and not message.is_read:
            message.is_read = True
            session.add(message)
    session.commit()
    session.refresh(conversation)

    return _create_conversation_read(conversation, current_user, session)

@router.post("/{conversation_id}/messages", response_model=MessageRead)
def send_message(
    conversation_id: int,
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    
    if not (conversation.teacher_id == current_user.id or conversation.student_id == current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send messages in this conversation.")
    
    if conversation.status == ConversationStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send messages in a closed conversation.")

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=message_in.content,
        is_read=False
    )
    session.add(message)
    conversation.updated_at = datetime.utcnow() # Update conversation timestamp
    session.add(conversation)
    session.commit()
    session.refresh(message)
    session.refresh(conversation)

    return MessageRead.model_validate(message)

@router.post("/{conversation_id}/close", response_model=ConversationRead)
def close_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    
    if conversation.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the teacher can close this conversation.")
    
    if conversation.status == ConversationStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation is already closed.")

    conversation.status = ConversationStatus.CLOSED
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    return _create_conversation_read(conversation, current_user, session)

@router.patch("/{conversation_id}/demo-video", response_model=ConversationRead)
def update_demo_video_url(
    conversation_id: int,
    demo_video_in: DemoVideoUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    
    if conversation.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the student can update the demo video URL.")
    
    conversation.student_demo_video_url = demo_video_in.url
    conversation.updated_at = datetime.utcnow()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    return _create_conversation_read(conversation, current_user, session)
