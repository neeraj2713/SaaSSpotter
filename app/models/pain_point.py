"""PainPoint / PainPointIdea document schemas."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import Field

from app.models.common import MongoModel, utc_now

CompetitionLevel = Literal["low", "medium", "high"]
MvpComplexity = Literal["weekend", "month", "quarter"]


class PainPointBase(MongoModel):
    original_post_id: str
    core_problem: str
    saas_idea_1: str
    saas_idea_2: str
    demand_score: int = Field(ge=1, le=10)
    industry_tag: str
    industry_tags: List[str] = Field(default_factory=list)
    cluster_slug: Optional[str] = None
    cluster_label: Optional[str] = None
    source_url: str
    target_customer: Optional[str] = None
    competition_level: Optional[CompetitionLevel] = None
    mvp_complexity: Optional[MvpComplexity] = None
    monetization_hint: Optional[str] = None
    evidence_quotes: List[str] = Field(default_factory=list)
    demand_score_rationale: List[str] = Field(default_factory=list)
    engagement_signal: Optional[str] = None
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=utc_now)


class PainPointCreate(PainPointBase):
    pass


class PainPointRead(PainPointBase):
    id: str = Field(alias="_id", serialization_alias="id")


class PainPointDetailRead(PainPointRead):
    source_excerpt: Optional[str] = None
    source_subreddit: Optional[str] = None
