from typing import List, Optional, Dict, Tuple
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import json

from ..database import get_session
from ..deps import get_current_user
from ..models import User, UserRole, Request, Conversation, ConversationStatus, Message
from ..security import decode_access_token

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Pydantic Schemas
class ConversationCreate(BaseModel):
    request_id: int

class MessageCreate(BaseModel):
    content: str
    replied_to_message_id: Optional[int] = None

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
    conversation_id: int
    sender_id: int
    content: str
    created_at: datetime
    is_read: bool
    sender_full_name: str
    sender_avatar_url: Optional[str] = None
    replied_to_message_id: Optional[int] = None
    replied_to_message_content: Optional[str] = None
    replied_to_sender_name: Optional[str] = None

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
    
    request_title: str
    teacher: UserPublicRead
    student: UserPublicRead
    messages: List[MessageRead] = []

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


# ConnectionManager for WebSockets
class ConnectionManager:
    def __init__(self):
        # Stores {conversation_id: [(websocket, user_id), ...]}
        self.active_conversation_connections: Dict[int, List[Tuple[WebSocket, int]]] = {}
        # Stores {user_id: [websocket, ...]} for global notifications
        self.active_user_connections: Dict[int, List[WebSocket]] = {}

    async def connect_conversation(self, websocket: WebSocket, conversation_id: int, user_id: int):
        await websocket.accept()
        if conversation_id not in self.active_conversation_connections:
            self.active_conversation_connections[conversation_id] = []
        self.active_conversation_connections[conversation_id].append((websocket, user_id))

    def disconnect_conversation(self, websocket: WebSocket, conversation_id: int, user_id: int):
        if conversation_id in self.active_conversation_connections:
            self.active_conversation_connections[conversation_id].remove((websocket, user_id))
            if not self.active_conversation_connections[conversation_id]:
                del self.active_conversation_connections[conversation_id]

    async def broadcast_to_conversation(self, message: str, conversation_id: int):
        if conversation_id in self.active_conversation_connections:
            for connection, _ in self.active_conversation_connections[conversation_id]:
                await connection.send_text(message)

    def is_user_in_conversation(self, user_id: int, conversation_id: int) -> bool:
        if conversation_id in self.active_conversation_connections:
            return any(uid == user_id for _, uid in self.active_conversation_connections[conversation_id])
        return False

    async def connect_user(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_user_connections:
            self.active_user_connections[user_id] = []
        self.active_user_connections[user_id].append(websocket)

    def disconnect_user(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_user_connections:
            self.active_user_connections[user_id].remove(websocket)
            if not self.active_user_connections[user_id]:
                del self.active_user_connections[user_id]

    async def send_user_notification(self, user_id: int, message: str):
        if user_id in self.active_user_connections:
            for connection in self.active_user_connections[user_id]:
                await connection.send_text(message)


manager = ConnectionManager()


# Helper to create ConversationRead from Conversation model
def _create_conversation_read(conversation: Conversation, current_user: User, session: Session) -> ConversationRead:
    # Ensure relationships are loaded
    if not conversation.request:
        conversation.request = session.get(Request, conversation.request_id)

    # Explicitly fetch teacher and student to avoid relationship loading bugs
    teacher = session.get(User, conversation.teacher_id)
    student = session.get(User, conversation.student_id)
    if not teacher or not student:
        raise HTTPException(status_code=500, detail="Could not load conversation participants.")
    messages_read = []
    for msg in conversation.messages:
        sender_user = session.get(User, msg.sender_id)
        replied_to_message_content = None
        replied_to_sender_name = None
        if msg.replied_to_message_id:
            replied_to_message = session.get(Message, msg.replied_to_message_id)
            if replied_to_message:
                replied_to_message_content = replied_to_message.content
                replied_to_sender = session.get(User, replied_to_message.sender_id)
                if replied_to_sender:
                    replied_to_sender_name = replied_to_sender.full_name

        messages_read.append(MessageRead(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            content=msg.content,
            created_at=msg.created_at,
            is_read=msg.is_read,
            sender_full_name=sender_user.full_name if sender_user else "Deleted User",
            sender_avatar_url=sender_user.avatar_url if sender_user else None,
            replied_to_message_id=msg.replied_to_message_id,
            replied_to_message_content=replied_to_message_content,
            replied_to_sender_name=replied_to_sender_name
        ))

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
        teacher=UserPublicRead.model_validate(teacher),
        student=UserPublicRead.model_validate(student),
        messages=messages_read
    )

# Helper to create ConversationSummaryRead from Conversation model
def _create_conversation_summary_read(conversation: Conversation, current_user: User, session: Session) -> ConversationSummaryRead:
    # Ensure relationships are loaded
    if not conversation.request:
        conversation.request = session.get(Request, conversation.request_id)

    # Explicitly determine and fetch the other participant to avoid relationship loading bugs
    other_participant_id = conversation.teacher_id if current_user.id == conversation.student_id else conversation.student_id
    other_participant = session.get(User, other_participant_id)
    if not other_participant:
        raise HTTPException(status_code=500, detail=f"Could not load other participant with ID {other_participant_id}.")

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
async def send_message(
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
        is_read=False,
        replied_to_message_id=message_in.replied_to_message_id
    )
    session.add(message)
    conversation.updated_at = datetime.utcnow() # Update conversation timestamp
    session.add(conversation)
    session.commit()
    session.refresh(message)
    session.refresh(conversation)

    # Prepare message for broadcast and return
    sender_user = session.get(User, message.sender_id)
    replied_to_message_content = None
    replied_to_sender_name = None
    if message.replied_to_message_id:
        replied_to_message = session.get(Message, message.replied_to_message_id)
        if replied_to_message:
            replied_to_message_content = replied_to_message.content
            replied_to_sender = session.get(User, replied_to_message.sender_id)
            if replied_to_sender:
                replied_to_sender_name = replied_to_sender.full_name

    message_read_instance = MessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content=message.content,
        created_at=message.created_at,
        is_read=message.is_read,
        sender_full_name=sender_user.full_name if sender_user else "Deleted User",
        sender_avatar_url=sender_user.avatar_url if sender_user else None,
        replied_to_message_id=message.replied_to_message_id,
        replied_to_message_content=replied_to_message_content,
        replied_to_sender_name=replied_to_sender_name
    )

    await manager.broadcast_to_conversation(message_read_instance.model_dump_json(), conversation_id)

    # Send notification to the other participant
    recipient_id = conversation.student_id if current_user.id == conversation.teacher_id else conversation.teacher_id
    if recipient_id != current_user.id:
        # Only send notification if the recipient is NOT currently in this conversation
        if not manager.is_user_in_conversation(recipient_id, conversation_id):
            # Calculate new unread count for the recipient
            unread_count = session.exec(
                select(func.count(Message.id))
                .where(Message.conversation_id == conversation.id)
                .where(Message.sender_id != recipient_id)
                .where(Message.is_read == False)
            ).one()
            notification_payload = json.dumps({"type": "UNREAD_COUNT_UPDATE", "unread_count": unread_count})
            await manager.send_user_notification(recipient_id, notification_payload)

    return message_read_instance

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

async def get_user_from_token(token: str, session: Session) -> Optional[User]:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return session.get(User, int(user_id))

@router.websocket("/{conversation_id}/ws")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int, token: str = Query(...), session: Session = Depends(get_session)):
    user = await get_user_from_token(token, session)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Check if user is part of this conversation
    conversation = session.get(Conversation, conversation_id)
    if not conversation or not (conversation.teacher_id == user.id or conversation.student_id == user.id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not authorized for this conversation")
        return

    await manager.connect_conversation(websocket, conversation_id, user.id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "READ_RECEIPT":
                    message_ids = payload.get("message_ids", [])
                    if message_ids:
                        # Update messages in bulk
                        stmt = select(Message).where(Message.id.in_(message_ids)).where(Message.sender_id != user.id)
                        messages_to_update = session.exec(stmt).all()
                        for msg in messages_to_update:
                            msg.is_read = True
                            session.add(msg)
                        session.commit()

                        # Recalculate total unread count for the user
                        total_unread_count = 0
                        user_conversations = session.exec(select(Conversation).where((Conversation.teacher_id == user.id) | (Conversation.student_id == user.id))).all()
                        for conv in user_conversations:
                            total_unread_count += session.exec(
                                select(func.count(Message.id))
                                .where(Message.conversation_id == conv.id)
                                .where(Message.sender_id != user.id)
                                .where(Message.is_read == False)
                            ).one()
                        
                        notification_payload = json.dumps({"type": "UNREAD_COUNT_UPDATE", "unread_count": total_unread_count})
                        await manager.send_user_notification(user.id, notification_payload)
            except json.JSONDecodeError:
                pass # Ignore non-JSON messages
    except WebSocketDisconnect:
        manager.disconnect_conversation(websocket, conversation_id, user.id)
    except Exception as e:
        print(f"WebSocket error in conversation {conversation_id}: {e}")
        manager.disconnect_conversation(websocket, conversation_id, user.id)


@router.websocket("/ws")
async def websocket_global_notifications_endpoint(websocket: WebSocket, token: str = Query(...), session: Session = Depends(get_session)):
    user = await get_user_from_token(token, session)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    await manager.connect_user(websocket, user.id)
    try:
        while True:
            # This endpoint is primarily for server-to-client notifications,
            # so we just keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user.id)
    except Exception as e:
        print(f"Global WebSocket error for user {user.id}: {e}")
        manager.disconnect_user(websocket, user.id)
