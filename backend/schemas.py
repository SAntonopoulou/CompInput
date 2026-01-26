from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from .models import UserRole, RequestStatus, MessageType, OfferStatus, ConversationStatus, ProjectStatus

class RequestCreate(BaseModel):
    title: str
    description: str
    language: str
    level: str
    budget: int = 0
    target_teacher_id: Optional[int] = None
    is_private: bool = False
    is_series: bool = False
    num_videos: Optional[int] = None

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
    is_private: bool
    created_at: datetime
    user_id: int
    user_name: str
    associated_project_id: Optional[int] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    project_funding_goal: Optional[int] = None
    tags: Optional[str] = None # Added tags field
    is_series: bool = False
    num_videos: Optional[int] = None

    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    title: str
    description: str
    language: str
    level: str
    funding_goal: int
    delivery_days: int
    tags: Optional[str] = None
    is_series: bool = False
    num_videos: Optional[int] = None
    price_per_video: Optional[int] = None

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

class UpdateCreate(BaseModel):
    content: str

class UpdateRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    project_id: int

    class Config:
        from_attributes = True

class BackerRead(BaseModel):
    id: int
    full_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class LanguageLevelsRead(BaseModel):
    language: str
    levels: List[str]

class FilterOptionsRead(BaseModel):
    languages: List[LanguageLevelsRead]

class ProjectRead(BaseModel):
    id: int
    title: str
    description: str
    language: str
    level: str
    tags: Optional[str] = None
    funding_goal: int
    current_funding: int
    deadline: Optional[datetime] = None
    delivery_days: Optional[int] = None
    status: ProjectStatus
    is_private: bool
    created_at: datetime
    updated_at: datetime
    teacher_id: int
    teacher_name: str
    teacher_avatar_url: Optional[str] = None
    origin_request_id: Optional[int] = None
    origin_request_title: Optional[str] = None
    origin_request_student_name: Optional[str] = None
    videos: List[str] = [] # Assuming list of video URLs or IDs
    is_backed_by_user: bool = False
    is_owner: bool = False
    is_teacher_verified: bool = False
    average_rating: Optional[float] = None
    total_ratings: int = 0
    is_series: bool = False
    num_videos: Optional[int] = None
    price_per_video: Optional[int] = None

    class Config:
        from_attributes = True

class PaginatedProjectRead(BaseModel):
    projects: List[ProjectRead]
    total_count: int

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    language: str
    level: str
    funding_goal: int
    status: ProjectStatus
    teacher_id: int
    origin_request_id: Optional[int] = None

    class Config:
        from_attributes = True

class CounterOffer(BaseModel):
    amount: int

class ConversationCreate(BaseModel):
    request_id: int

class MessageCreate(BaseModel):
    content: str
    replied_to_message_id: Optional[int] = None

class OfferCreate(BaseModel):
    offer_description: str
    offer_price: int
    title: str
    language: str
    level: str
    tags: Optional[str] = None
    is_series: Optional[bool] = None
    num_videos: Optional[int] = None
    price_per_video: Optional[int] = None

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
    message_type: MessageType
    offer_description: Optional[str] = None
    offer_price: Optional[int] = None
    offer_status: Optional[OfferStatus] = None
    offer_title: Optional[str] = None
    offer_language: Optional[str] = None
    offer_level: Optional[str] = None
    offer_tags: Optional[str] = None
    offer_is_series: Optional[bool] = None
    offer_num_videos: Optional[int] = None
    offer_price_per_video: Optional[int] = None

    class Config:
        from_attributes = True

class ConversationRead(BaseModel):
    id: int
    request_id: int
    teacher_id: int
    student_id: int
    status: ConversationStatus
    student_demo_video_url: Optional[str] = None
    demo_video_requested: bool = False
    created_at: datetime
    updated_at: datetime
    
    request: RequestRead
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