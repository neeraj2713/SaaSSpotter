"""User-scoped endpoints (requires Clerk JWT)."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import PyMongoError

from app.api.deps import (
    get_pain_point_repo,
    get_user_saved_repo,
    get_user_visits_repo,
    get_user_watches_repo,
)
from app.core.clerk_auth import get_current_user_id
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.db.repositories.pain_points import PainPointRepository
from app.db.repositories.user_saved import UserSavedRepository
from app.db.repositories.user_visits import UserVisitsRepository
from app.db.repositories.user_watches import UserWatchesRepository
from app.models.user import (
    AlertWatchCreate,
    AlertWatchRead,
    SavedIdsResponse,
    UserVisitRead,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


def _handle_db_error(exc: Exception) -> None:
    logger.exception("Database error")
    raise ServiceUnavailableError("Database unavailable") from exc


@router.get("/saved", response_model=SavedIdsResponse)
def list_saved(
    user_id: str = Depends(get_current_user_id),
    repo: UserSavedRepository = Depends(get_user_saved_repo),
) -> SavedIdsResponse:
    try:
        return SavedIdsResponse(ids=repo.list_ids(user_id))
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.post("/saved/{pain_point_id}", status_code=204)
def save_idea(
    pain_point_id: str,
    user_id: str = Depends(get_current_user_id),
    saved_repo: UserSavedRepository = Depends(get_user_saved_repo),
    pain_point_repo: PainPointRepository = Depends(get_pain_point_repo),
):
    try:
        if pain_point_repo.find_by_id(pain_point_id) is None:
            raise NotFoundError("Pain point not found")
        saved_repo.save(user_id, pain_point_id)
    except NotFoundError:
        raise
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.delete("/saved/{pain_point_id}", status_code=204)
def unsave_idea(
    pain_point_id: str,
    user_id: str = Depends(get_current_user_id),
    repo: UserSavedRepository = Depends(get_user_saved_repo),
):
    try:
        repo.unsave(user_id, pain_point_id)
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.get("/watches", response_model=list[AlertWatchRead])
def list_watches(
    user_id: str = Depends(get_current_user_id),
    repo: UserWatchesRepository = Depends(get_user_watches_repo),
) -> list[AlertWatchRead]:
    try:
        return repo.list_watches(user_id)
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.post("/watches", response_model=AlertWatchRead, status_code=201)
def create_watch(
    body: AlertWatchCreate,
    user_id: str = Depends(get_current_user_id),
    repo: UserWatchesRepository = Depends(get_user_watches_repo),
) -> AlertWatchRead:
    if not body.keywords and not body.tags:
        raise HTTPException(status_code=400, detail="Provide keywords or tags")
    try:
        return repo.create_watch(user_id, body)
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.delete("/watches/{watch_id}", status_code=204)
def delete_watch(
    watch_id: str,
    user_id: str = Depends(get_current_user_id),
    repo: UserWatchesRepository = Depends(get_user_watches_repo),
):
    try:
        if not repo.delete_watch(user_id, watch_id):
            raise NotFoundError("Watch not found")
    except NotFoundError:
        raise
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.get("/visit", response_model=UserVisitRead)
def get_visit(
    user_id: str = Depends(get_current_user_id),
    repo: UserVisitsRepository = Depends(get_user_visits_repo),
) -> UserVisitRead:
    try:
        return UserVisitRead(last_visited_at=repo.get_last_visited(user_id))
    except PyMongoError as exc:
        _handle_db_error(exc)


@router.post("/visit", response_model=UserVisitRead)
def touch_visit(
    user_id: str = Depends(get_current_user_id),
    repo: UserVisitsRepository = Depends(get_user_visits_repo),
) -> UserVisitRead:
    try:
        return UserVisitRead(last_visited_at=repo.touch(user_id))
    except PyMongoError as exc:
        _handle_db_error(exc)
