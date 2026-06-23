"""Pain cluster endpoints."""

import logging

from fastapi import APIRouter, Depends
from pymongo.errors import PyMongoError

from app.api.deps import get_pain_point_repo
from app.core.exceptions import ServiceUnavailableError
from app.db.repositories.pain_points import PainPointRepository
from app.models.cluster import ClustersResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=ClustersResponse)
def list_clusters(
    repo: PainPointRepository = Depends(get_pain_point_repo),
) -> ClustersResponse:
    try:
        return ClustersResponse(clusters=repo.aggregate_clusters())
    except PyMongoError as exc:
        logger.exception("MongoDB error listing clusters")
        raise ServiceUnavailableError("Database unavailable") from exc
