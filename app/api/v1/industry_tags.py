"""Industry tag endpoints."""

import logging

from fastapi import APIRouter, Depends
from pymongo.errors import PyMongoError

from app.api.deps import get_pain_point_repo
from app.core.exceptions import ServiceUnavailableError
from app.db.repositories.pain_points import PainPointRepository
from app.models.industry_tag import IndustryTagsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/industry-tags", tags=["industry-tags"])


@router.get("", response_model=IndustryTagsResponse)
def list_industry_tags(
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> IndustryTagsResponse:
    """Return distinct industry tags with counts."""
    try:
        tags = repo.aggregate_industry_tags()
    except PyMongoError as exc:
        logger.exception("MongoDB error listing industry tags")
        raise ServiceUnavailableError("Database unavailable") from exc
    except Exception as exc:
        logger.exception("Unexpected error listing industry tags")
        raise ServiceUnavailableError("Database unavailable") from exc

    return IndustryTagsResponse(tags=tags)
