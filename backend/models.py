from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# Enums for strict state management
class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MODERATOR = "moderator"
    ADMIN = "admin"

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"       # Funding is live
    FUNDED = "funded"       # Goal met, waiting for video
    IN_PROGRESS = "in_progress" # Teacher started working
    COMPLETED = "completed" # Video delivered
    CANCELLED = "cancelled" # Refunded or expired

class PledgeStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized" # Money held
    CAPTURED = "captured"     # Money taken (project funded)
    REFUNDED = "refunded"

class RequestStatus(str, Enum):
    OPEN = "open"
    NEGOTIATING = "negotiating"
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
    languages: Optional[str] = None # Comma-separated string
    intro_video_url: Optional[str] = None
    sample_video_url: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Stripe fields
    stripe_customer_id: Optional[str] = None # For paying students
    stripe_account_id: Optional[str] = None  # For receiving teachers
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    projects: List["Project"] = Relationship(back_populates="teacher")
    pledges: List["Pledge"] = Relationship(back_populates="user")
    notifications: List["Notification"] = Relationship(back_populates="user")
    requests: List["Request"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "Request.user_id"}
    )
    ratings: List["VideoRating"] = Relationship(back_populates="user")
    video_comments: List["VideoComment"] = Relationship(back_populates="user")

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    language: str = Field(index=True)
    level: str = Field(index=True) # e.g. "N3", "B1"
    tags: Optional[str] = Field(default=None) # Comma-separated string
    
    goal_amount: int # Stored in cents (e.g. 1000 = $10.00) to avoid float errors
    current_amount: int = Field(default=0)
    
    deadline: Optional[datetime] = None
    delivery_days: Optional[int] = None # Number of days to deliver after funding
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)
    
    # For custom/private videos
    is_private: bool = Field(default=False)
    
    # Payout info
    stripe_transfer_id: Optional[str] = None
    origin_request_id: Optional[int] = Field(default=None, foreign_key="request.id") # Link back to the request
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    teacher_id: Optional[int] = Field(default=None, foreign_key="user.id")
    teacher: Optional[User] = Relationship(back_populates="projects")
    
    request: Optional["Request"] = Relationship(sa_relationship_kwargs={"foreign_keys": "Project.origin_request_id"})
    
    videos: List["Video"] = Relationship(back_populates="project")
    pledges: List["Pledge"] = Relationship(back_populates="project")
    updates: List["ProjectUpdate"] = Relationship(back_populates="project")

class ProjectUpdate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project_id: int = Field(foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="updates")

class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str
    platform: str = Field(default="youtube") # youtube, vimeo, etc.
    duration: Optional[int] = None # in seconds
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="videos")
    
    ratings: List["VideoRating"] = Relationship(back_populates="video")
    comments: List["VideoComment"] = Relationship(back_populates="video")

class VideoRating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rating: int # 1-5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="ratings")
    
    video_id: Optional[int] = Field(default=None, foreign_key="video.id")
    video: Optional[Video] = Relationship(back_populates="ratings")

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
    amount: int # in cents
    status: PledgeStatus = Field(default=PledgeStatus.PENDING)
    
    stripe_payment_intent_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="pledges")
    
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="pledges")

class Request(SQLModel, table=True):
    """
    Requests made by students for specific content.
    Teachers can browse these and offer to fulfill them (creating a Project).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    language: str
    level: str
    
    budget: int = Field(default=0) # in cents
    target_teacher_id: Optional[int] = Field(default=None, foreign_key="user.id")
    counter_offer_amount: Optional[int] = None # in cents
    status: RequestStatus = Field(default=RequestStatus.OPEN)
    is_private: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(
        back_populates="requests",
        sa_relationship_kwargs={"foreign_keys": "Request.user_id"}
    )

    target_teacher: Optional[User] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Request.target_teacher_id"}
    )

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