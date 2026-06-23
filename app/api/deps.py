"""FastAPI dependency injection."""

from app.core.config import Settings, get_settings
from app.db.mongodb import get_database
from app.db.repositories.pain_points import PainPointRepository
from app.db.repositories.raw_posts import RawPostRepository
from app.services.pipeline_service import PipelineService


def get_app_settings() -> Settings:
    return get_settings()


def get_pain_point_repo() -> PainPointRepository:
    return PainPointRepository(get_database())


def get_raw_post_repo() -> RawPostRepository:
    return RawPostRepository(get_database())


def get_pipeline_service() -> PipelineService:
    return PipelineService(get_settings())
