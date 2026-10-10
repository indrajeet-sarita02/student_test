"""Test-assignment schemas (which student may take which test).

Defines the single-assignment request, the bulk-assignment request required by
``POST /assignments/bulk`` (``TestAssignmentBulkRequest``) and the enriched
response carrying the denormalised test/student names.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    """Body for ``POST /assignments``."""

    test_id: int = Field(..., ge=1, description="Test to assign.")
    student_id: int = Field(..., ge=1, description="User id of the student.")
    available_from: Optional[datetime] = Field(
        None, description="Optional UTC start of the availability window."
    )
    available_until: Optional[datetime] = Field(
        None, description="Optional UTC end of the availability window."
    )
    max_attempts: Optional[int] = Field(
        None, ge=1, le=100, description="Per-assignment attempt override."
    )


class TestAssignmentBulkRequest(BaseModel):
    """Body for ``POST /assignments/bulk``."""

    test_id: int = Field(..., ge=1, description="Test to assign.")
    student_ids: List[int] = Field(
        ..., min_length=1, max_length=1000, description="Student user ids."
    )
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    max_attempts: Optional[int] = Field(None, ge=1, le=100)


#: Backwards-compatible alias for callers that used the earlier name.
AssignmentBulkCreate = TestAssignmentBulkRequest


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    student_id: int
    assigned_at: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    max_attempts: Optional[int] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    test_name: Optional[str] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None


class AssignmentBulkResponse(BaseModel):
    """Result of a bulk assignment: how many were created vs. skipped."""

    created: int = 0
    skipped: int = 0
    assignments: List[AssignmentResponse] = Field(default_factory=list)
