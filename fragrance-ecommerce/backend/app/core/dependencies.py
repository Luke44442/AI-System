from __future__ import annotations
from typing import Optional
from fastapi import Query
from app.schemas.common import PaginationParams, SortParams


def get_pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def get_sort(
    sort_by: Optional[str] = Query(default=None),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> SortParams:
    return SortParams(sort_by=sort_by, sort_dir=sort_dir)
