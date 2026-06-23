"""Pain points feed endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pymongo.errors import PyMongoError

from app.api.deps import get_pain_point_repo
from app.core.exceptions import ServiceUnavailableError
from app.db.repositories.pain_points import PainPointRepository
from app.models.common import PaginatedResponse
from app.models.pain_point import PainPointRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/painpoints", tags=["painpoints"])


@router.get("", response_model=PaginatedResponse[PainPointRead])
def list_pain_points(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    industry_tag: Optional[str] = Query(default=None),
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> PaginatedResponse[PainPointRead]:
    """Fetch paginated pain points and Micro-SaaS ideas."""
    try:
        items, total = repo.find_paginated(
            page=page,
            page_size=page_size,
            industry_tag=industry_tag,
        )
    except PyMongoError as exc:
        logger.exception("MongoDB error listing pain points")
        raise ServiceUnavailableError("Database unavailable") from exc
    except Exception as exc:
        logger.exception("Unexpected error listing pain points")
        raise ServiceUnavailableError("Database unavailable") from exc

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )
