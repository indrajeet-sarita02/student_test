"""Subject schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    exam_id: int
    name: str = Field(..., min_length=2, max_length=150, examples=["Physics"])
    code: str = Field(..., min_length=1, max_length=50, examples=["PHY"])
    description: Optional[str] = None
    sort_order: int = Field(0, ge=0, le=9999)


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0, le=9999)
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    name: str
    code: str
    description: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
