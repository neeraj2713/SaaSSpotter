"""PainPoint / PainPointIdea document schemas."""

from datetime import datetime

from pydantic import Field

from app.models.common import MongoModel, utc_now


class PainPointBase(MongoModel):
    original_post_id: str
    core_problem: str
    saas_idea_1: str
    saas_idea_2: str
    demand_score: int = Field(ge=1, le=10)
    industry_tag: str
    source_url: str
    created_at: datetime = Field(default_factory=utc_now)


class PainPointCreate(PainPointBase):
    pass


class PainPointRead(PainPointBase):
    id: str = Field(alias="_id")
