"""Weekly digest endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pymongo.errors import PyMongoError

from app.api.deps import get_pain_point_repo
from app.core.exceptions import ServiceUnavailableError
from app.db.repositories.pain_points import PainPointRepository
from app.models.digest import DigestResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("", response_model=DigestResponse)
def get_digest(
    days: int = Query(default=7, ge=1, le=30),
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> DigestResponse:
    try:
        since = datetime.utcnow() - timedelta(days=days)
        return DigestResponse(
            period_days=days,
            new_count=repo.count_since(since),
            top_by_demand=repo.find_top_by_demand(limit=5, since=since),
            trending=repo.find_trending(limit=5),
            top_clusters=repo.aggregate_clusters(limit=5),
        )
    except PyMongoError as exc:
        logger.exception("MongoDB error building digest")
        raise ServiceUnavailableError("Database unavailable") from exc
