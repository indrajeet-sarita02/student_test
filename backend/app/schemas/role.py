"""Role schemas."""

from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.permission import PermissionResponse


class RoleBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Examiner"])
    code: str = Field(
        ..., min_length=2, max_length=50, pattern=r"^[A-Za-z0-9_]+$", examples=["EXAMINER"]
    )
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    permission_ids: List[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class RolePermissionsUpdate(BaseModel):
    permission_ids: List[int] = Field(default_factory=list)


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_system_role: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = Field(default_factory=list)
