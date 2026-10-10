"""Permission schemas."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    module: str
    action: str
    description: Optional[str] = None


class PermissionModuleResponse(BaseModel):
    module: str
    permissions: list[PermissionResponse] = Field(default_factory=list)
