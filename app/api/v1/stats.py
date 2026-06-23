"""Platform stats endpoints."""

import logging

from fastapi import APIRouter, Depends
from pymongo.errors import PyMongoError

from app.api.deps import get_meta_repo, get_pain_point_repo
from app.core.exceptions import ServiceUnavailableError
from app.db.repositories.meta import MetaRepository
from app.db.repositories.pain_points import PainPointRepository
from app.models.stats import StatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def get_stats(
    pain_point_repo: PainPointRepository = Depends(get_pain_point_repo),
    meta_repo: MetaRepository = Depends(get_meta_repo),
) -> StatsResponse:
    """Return platform statistics."""
    try:
        return StatsResponse(
            last_scrape_at=meta_repo.get_last_scrape_at(),
            total_pain_points=pain_point_repo.count_all(),
        )
    except PyMongoError as exc:
        logger.exception("MongoDB error fetching stats")
        raise ServiceUnavailableError("Database unavailable") from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching stats")
        raise ServiceUnavailableError("Database unavailable") from exc
