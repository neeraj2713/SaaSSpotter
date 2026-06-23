"""Shared Pydantic utilities."""

from datetime import datetime
from typing import Generic, List, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class MongoModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class PipelineResult(BaseModel):
    scraped_count: int = 0
    unprocessed_ids: List[str] = Field(default_factory=list)


class ScrapeResult(BaseModel):
    scraped_count: int = 0
    unprocessed_ids: List[str] = Field(default_factory=list)


class ProcessResult(BaseModel):
    raw_post_id: str
    processed: bool = False
    is_valid_pain_point: bool = False
    pain_point_id: str | None = None
    skipped_reason: str | None = None


class FilterResult(BaseModel):
    is_valid: bool
    confidence: float = 0.0
    reason: str = ""


class IdeaResult(BaseModel):
    core_problem: str
    saas_idea_1: str
    saas_idea_2: str
    demand_score: int = Field(ge=1, le=10)
    industry_tag: str
    industry_tags: List[str] = Field(default_factory=list)
    cluster_slug: str = ""
    cluster_label: str = ""
    target_customer: str = ""
    competition_level: Literal["low", "medium", "high"] = "medium"
    mvp_complexity: Literal["weekend", "month", "quarter"] = "month"
    monetization_hint: str = ""
    evidence_quotes: List[str] = Field(default_factory=list)
    demand_score_rationale: List[str] = Field(default_factory=list)
    engagement_signal: str = ""


def utc_now() -> datetime:
    return datetime.utcnow()
