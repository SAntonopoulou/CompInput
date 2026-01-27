from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# Enums
class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MODERATOR = "moderator"
    ADMIN = "admin"

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    FUNDING = "funding"
    SUCCESSFUL = "successful"
    PENDING_CONFIRMATION = "pending_confirmation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class PledgeStatus(str, Enum):
    PENDING = "pending"
    CAPTURED = "captured"
    REFUNDED = "refunded"

class RequestStatus(str, Enum):
    OPEN = "open"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ConversationStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class MessageType(str, Enum):
    TEXT = "text"
    OFFER = "offer"
    DEMO_REQUEST = "demo_request"
    DEMO_VIDEO = "demo_video"

class OfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

# Database Models

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    role: UserRole = Field(default=UserRole.STUDENT)
    bio: Optional[str] = None
    languages: Optional[str] = None
    intro_video_url: Optional[str] = None
    sample_video_url: Optional[str] = None
    avatar_url: Optional[str] = None
    
    stripe_customer_id: Optional[str] = None
    stripe_account_id: Optional[str] = None
    charges_enabled: bool = Field(default=False)
    payouts_enabled: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    taught_projects: List["Project"] = Relationship(back_populates="teacher")
    pledges: List["Pledge"] = Relationship(back_populates="user")
    notifications: List["Notification"] = Relationship(back_populates="user")
    requests: List["Request"] = Relationship(back_populates="user", sa_relationship_kwargs={"foreign_keys": "Request.user_id"})
    project_ratings: List["ProjectRating"] = Relationship(back_populates="user")
    video_comments: List["VideoComment"] = Relationship(back_populates="user")
    verifications: List["TeacherVerification"] = Relationship(back_populates="teacher")

    # New relationships for messaging
    sent_messages: List["Message"] = Relationship(back_populates="sender")
    conversations_as_teacher: List["Conversation"] = Relationship(back_populates="teacher", sa_relationship_kwargs={"foreign_keys": "Conversation.teacher_id"})
    conversations_as_student: List["Conversation"] = Relationship(back_populates="student", sa_relationship_kwargs={"foreign_keys": "Conversation.student_id"})


class TeacherVerification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    language: str
    document_url: str
    status: VerificationStatus = Field(default=VerificationStatus.PENDING)
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    
    teacher_id: int = Field(foreign_key="user.id")
    teacher: "User" = Relationship(back_populates="verifications")

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    language: str = Field(index=True)
    level: str = Field(index=True)
    tags: Optional[str] = None
    
    funding_goal: int
    current_funding: int = Field(default=0)
    total_tipped_amount: int = Field(default=0)
    
    deadline: Optional[datetime] = None
    delivery_days: Optional[int] = None
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)
    
    is_private: bool = Field(default=False)
    
    stripe_transfer_id: Optional[str] = None
    origin_request_id: Optional[int] = Field(default=None, foreign_key="request.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    funded_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    
    teacher_id: Optional[int] = Field(default=None, foreign_key="user.id")
    teacher: Optional[User] = Relationship(back_populates="taught_projects")
    
    request: Optional["Request"] = Relationship(sa_relationship_kwargs={"foreign_keys": "Project.origin_request_id"})
    
    videos: List["Video"] = Relationship(back_populates="project")
    pledges: List["Pledge"] = Relationship(back_populates="project")
    updates: List["ProjectUpdate"] = Relationship(back_populates="project")
    ratings: List["ProjectRating"] = Relationship(back_populates="project")

    # New fields for multi-video projects
    is_series: bool = Field(default=False)
    num_videos: Optional[int] = None
    price_per_video: Optional[int] = None
    project_image_url: Optional[str] = None
    series_intro_video_url: Optional[str] = None

class ProjectUpdate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project_id: int = Field(foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="updates")

class VideoResource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str
    video_id: int = Field(foreign_key="video.id")
    video: "Video" = Relationship(back_populates="resources")

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str
    platform: str = Field(default="youtube")
    duration: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="videos")
    
    comments: List["VideoComment"] = Relationship(back_populates="video")
    resources: List["VideoResource"] = Relationship(back_populates="video")

class ProjectRating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    teacher_response: Optional[str] = None
    response_created_at: Optional[datetime] = None
    
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="project_ratings")
    
    project_id: int = Field(foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="ratings")

class VideoComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="video_comments")
    
    video_id: int = Field(foreign_key="video.id")
    video: Optional[Video] = Relationship(back_populates="comments")

class Pledge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: int
    status: PledgeStatus = Field(default=PledgeStatus.PENDING)
    
    checkout_session_id: Optional[str] = Field(default=None, unique=True, index=True, nullable=True)
    payment_intent_id: Optional[str] = Field(default=None, unique=True, index=True, nullable=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="pledges")
    
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="pledges")

class Request(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    language: str
    level: str
    
    budget: int = Field(default=0)
    target_teacher_id: Optional[int] = Field(default=None, foreign_key="user.id")
    counter_offer_amount: Optional[int] = None
    status: RequestStatus = Field(default=RequestStatus.OPEN)
    is_private: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="requests", sa_relationship_kwargs={"foreign_keys": "Request.user_id"})

    target_teacher: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "Request.target_teacher_id"})
    conversations: List["Conversation"] = Relationship(back_populates="request")

    # New fields for multi-video requests
    is_series: bool = Field(default=False)
    num_videos: Optional[int] = None

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    is_read: bool = Field(default=False)
    link: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="notifications")

class RequestBlacklist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="request.id")
    teacher_id: int = Field(foreign_key="user.id")

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: int = Field(foreign_key="request.id", index=True)
    teacher_id: int = Field(foreign_key="user.id", index=True)
    student_id: int = Field(foreign_key="user.id", index=True)
    status: ConversationStatus = Field(default=ConversationStatus.OPEN)
    student_demo_video_url: Optional[str] = None
    demo_video_requested: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    request: Optional["Request"] = Relationship(back_populates="conversations")
    teacher: Optional["User"] = Relationship(back_populates="conversations_as_teacher", sa_relationship_kwargs={"foreign_keys": "Conversation.teacher_id"})
    student: Optional["User"] = Relationship(back_populates="conversations_as_student", sa_relationship_kwargs={"foreign_keys": "Conversation.student_id"})
    messages: List["Message"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "Message.created_at"})

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    sender_id: int = Field(foreign_key="user.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)
    replied_to_message_id: Optional[int] = Field(default=None, foreign_key="message.id")

    message_type: MessageType = Field(default=MessageType.TEXT)
    offer_description: Optional[str] = None
    offer_price: Optional[int] = None
    offer_status: Optional[OfferStatus] = Field(default=None)
    offer_title: Optional[str] = None
    offer_language: Optional[str] = None
    offer_level: Optional[str] = None
    offer_tags: Optional[str] = None

    # New fields for multi-video offers
    offer_is_series: Optional[bool] = None
    offer_num_videos: Optional[int] = None
    offer_price_per_video: Optional[int] = None

    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
    sender: Optional["User"] = Relationship(back_populates="sent_messages")
    replied_to_message: Optional["Message"] = Relationship(sa_relationship_kwargs={"remote_side": "Message.id"})