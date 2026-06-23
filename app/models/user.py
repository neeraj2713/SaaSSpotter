"""User-scoped document schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.common import MongoModel, utc_now


class SavedIdsResponse(BaseModel):
    ids: List[str]


class AlertWatchCreate(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    label: Optional[str] = None


class AlertWatchRead(MongoModel):
    id: str = Field(alias="_id", serialization_alias="id")
    user_id: str
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    label: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class UserVisitRead(BaseModel):
    last_visited_at: datetime | None = None


class PainPointBatchRequest(BaseModel):
    ids: List[str] = Field(min_length=1, max_length=50)
