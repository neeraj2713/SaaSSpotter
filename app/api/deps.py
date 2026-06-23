"""FastAPI dependency injection."""

from app.core.config import Settings, get_settings
from app.db.mongodb import get_database
from app.db.repositories.meta import MetaRepository
from app.db.repositories.pain_point_scores import PainPointScoreRepository
from app.db.repositories.pain_points import PainPointRepository
from app.db.repositories.raw_posts import RawPostRepository
from app.db.repositories.user_saved import UserSavedRepository
from app.db.repositories.user_visits import UserVisitsRepository
from app.db.repositories.user_watches import UserWatchesRepository
from app.services.pipeline_service import PipelineService


def get_app_settings() -> Settings:
    return get_settings()


def get_pain_point_repo() -> PainPointRepository:
    return PainPointRepository(get_database())


def get_meta_repo() -> MetaRepository:
    return MetaRepository(get_database())


def get_pain_point_score_repo() -> PainPointScoreRepository:
    return PainPointScoreRepository(get_database())


def get_raw_post_repo() -> RawPostRepository:
    return RawPostRepository(get_database())


def get_user_saved_repo() -> UserSavedRepository:
    return UserSavedRepository(get_database())


def get_user_watches_repo() -> UserWatchesRepository:
    return UserWatchesRepository(get_database())


def get_user_visits_repo() -> UserVisitsRepository:
    return UserVisitsRepository(get_database())


def get_pipeline_service() -> PipelineService:
    return PipelineService(get_settings())
