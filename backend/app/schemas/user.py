"""User, student profile and role-assignment schemas."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.role import RoleBrief
from app.utils.enums import Gender, UserStatus


class StudentProfileCreate(BaseModel):
    student_code: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    institution: Optional[str] = Field(None, max_length=200)
    class_name: Optional[str] = Field(None, max_length=50, alias="class")
    roll_number: Optional[str] = Field(None, max_length=50)

    model_config = ConfigDict(populate_by_name=True)


class StudentProfileUpdate(StudentProfileCreate):
    pass


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    student_code: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    institution: Optional[str] = None
    class_name: Optional[str] = Field(None, alias="class")
    roll_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    mobile: Optional[str] = Field(None, max_length=30)
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False
    role_ids: List[int] = Field(default_factory=list)
    student_profile: Optional[StudentProfileCreate] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    mobile: Optional[str] = Field(None, max_length=30)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_verified: Optional[bool] = None
    student_profile: Optional[StudentProfileUpdate] = None


class UserStatusUpdate(BaseModel):
    status: UserStatus


class AssignRolesRequest(BaseModel):
    role_ids: List[int] = Field(default_factory=list)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    status: str
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    roles: List[RoleBrief] = Field(default_factory=list)
    student_profile: Optional[StudentProfileResponse] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class UserPermissionsResponse(BaseModel):
    user_id: int
    permissions: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
