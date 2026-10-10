"""Pagination helpers used by every list endpoint.

Query contract::

    ?page=1&page_size=20&search=neet&status=published&sort_by=created_at&sort_order=desc

Response contract::

    {"items": [], "page": 1, "page_size": 20, "total": 100, "total_pages": 5}
"""

import math
from typing import Any, Generic, List, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

ItemT = TypeVar("ItemT")

MAX_PAGE_SIZE = 100


class PaginationParams:
    """FastAPI dependency describing page/sort/filter parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number, starting from 1."),
        page_size: int = Query(
            20, ge=1, le=MAX_PAGE_SIZE, description="Items per page (max 100)."
        ),
        search: Optional[str] = Query(None, description="Free-text search keyword."),
        status: Optional[str] = Query(None, description="Filter by status."),
        sort_by: Optional[str] = Query(None, description="Column to sort by."),
        sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction."),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.search = search.strip() if search else None
        self.status = status.strip().upper() if status else None
        self.sort_by = sort_by
        self.sort_order = sort_by and sort_order or None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page(BaseModel, Generic[ItemT]):
    items: List[ItemT]
    page: int
    page_size: int
    total: int
    total_pages: int


def build_page(items: Sequence[Any], page: int, page_size: int, total: int) -> Any:
    return {
        "items": list(items),
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size) if total else 0,
    }


def paginate(
    db: Session,
    stmt: Select,
    params: PaginationParams,
) -> Any:
    """Apply ``LIMIT/OFFSET`` plus ``total``/``total_pages`` to a select statement."""
    total = db.scalar(select_count(stmt)) or 0
    rows = db.scalars(stmt.offset(params.offset).limit(params.limit)).all()
    return build_page(rows, params.page, params.page_size, total)


def select_count(stmt: Select) -> Select:
    """Wrap a select in a COUNT(*) sub-select, keeping only its WHERE clause."""
    return select(func.count()).select_from(stmt.order_by(None).subquery())
