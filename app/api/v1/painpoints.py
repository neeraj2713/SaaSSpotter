"""Pain points feed endpoints."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pymongo.errors import PyMongoError

from app.api.deps import get_pain_point_repo, get_pain_point_score_repo, get_raw_post_repo
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.db.repositories.pain_point_scores import PainPointScoreRepository
from app.db.repositories.pain_points import PainPointRepository, SortField, SortOrder
from app.db.repositories.raw_posts import RawPostRepository
from app.models.common import PaginatedResponse
from app.models.pain_point import PainPointDetailRead, PainPointRead
from app.models.pain_point_score import PainPointScoreRead
from app.models.user import PainPointBatchRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/painpoints", tags=["painpoints"])


def _handle_db_error(exc: Exception) -> None:
    logger.exception("Database error")
    raise ServiceUnavailableError("Database unavailable") from exc


@router.get("", response_model=PaginatedResponse[PainPointRead])
def list_pain_points(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    industry_tag: Optional[str] = Query(default=None),
    cluster: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=200),
    sort: SortField = Query(default="created_at"),
    order: SortOrder = Query(default="desc"),
    trending: bool = Query(default=False),
    since: Optional[datetime] = Query(default=None),
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> PaginatedResponse[PainPointRead]:
    """Fetch paginated pain points and Micro-SaaS ideas."""
    try:
        items, total = repo.find_paginated(
            page=page,
            page_size=page_size,
            industry_tag=industry_tag,
            cluster_slug=cluster,
            q=q,
            sort=sort,
            order=order,
            trending=trending,
            since=since,
        )
    except PyMongoError as exc:
        _handle_db_error(exc)
    except Exception as exc:
        _handle_db_error(exc)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.post("/batch", response_model=List[PainPointRead])
def batch_pain_points(
    body: PainPointBatchRequest,
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> List[PainPointRead]:
    try:
        return repo.find_by_ids(body.ids)
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.get("/{pain_point_id}", response_model=PainPointDetailRead)
def get_pain_point(
    pain_point_id: str,
    repo: PainPointRepository = Depends(get_pain_point_repo),
    raw_repo: RawPostRepository = Depends(get_raw_post_repo),
) -> PainPointDetailRead:
    """Fetch a single pain point by ID with source excerpt."""
    try:
        item = repo.find_by_id(pain_point_id)
    except PyMongoError as exc:
        _handle_db_error(exc)
    except Exception as exc:
        _handle_db_error(exc)

    if item is None:
        raise NotFoundError("Pain point not found")

    detail = PainPointDetailRead.model_validate(item.model_dump())
    raw_post = raw_repo.find_by_id(item.original_post_id)
    if raw_post:
        detail.source_excerpt = raw_post.text[:600]
        detail.source_subreddit = raw_post.subreddit
    return detail


@router.get("/{pain_point_id}/score-history", response_model=List[PainPointScoreRead])
def get_pain_point_score_history(
    pain_point_id: str,
    limit: int = Query(default=30, ge=1, le=100),
    pain_point_repo: PainPointRepository = Depends(get_pain_point_repo),
    score_repo: PainPointScoreRepository = Depends(get_pain_point_score_repo),
) -> List[PainPointScoreRead]:
    try:
        source = pain_point_repo.find_by_id(pain_point_id)
        if source is None:
            raise NotFoundError("Pain point not found")
        return score_repo.find_by_pain_point_id(pain_point_id, limit=limit)
    except NotFoundError:
        raise
    except PyMongoError as exc:
        _handle_db_error(exc)
    except Exception as exc:
        _handle_db_error(exc)


@router.get("/{pain_point_id}/similar", response_model=List[PainPointRead])
def get_similar_pain_points(
    pain_point_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> List[PainPointRead]:
    try:
        source = repo.find_by_id(pain_point_id)
        if source is None:
            raise NotFoundError("Pain point not found")
        return repo.find_similar(pain_point_id, limit=limit)
    except NotFoundError:
        raise
    except PyMongoError as exc:
        _handle_db_error(exc)
    except Exception as exc:
        _handle_db_error(exc)
