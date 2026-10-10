"""Topic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TopicCreate(BaseModel):
    subject_id: int
    parent_topic_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=150, examples=["Kinematics"])
    description: Optional[str] = None
    sort_order: int = Field(0, ge=0, le=9999)


class TopicUpdate(BaseModel):
    parent_topic_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0, le=9999)
    is_active: Optional[bool] = None


class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    parent_topic_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
