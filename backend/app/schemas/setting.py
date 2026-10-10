"""Runtime setting schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SettingUpdate(BaseModel):
    setting_value: str = Field(..., description="New value stored as text.")
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = Field(
        None, description="When true the value is readable without authentication."
    )


class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    setting_key: str
    setting_value: Optional[str] = None
    description: Optional[str] = None
    is_public: bool
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
