"""RawPost document schemas."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.common import MongoModel, utc_now


class RawPostBase(MongoModel):
    source: str = "firecrawl"
    source_id: str
    text: str
    url: str
    subreddit: str
    created_at: datetime
    scraped_at: datetime = Field(default_factory=utc_now)
    processed_at: Optional[datetime] = None


class RawPostCreate(RawPostBase):
    pass


class RawPostRead(RawPostBase):
    id: str = Field(alias="_id")
