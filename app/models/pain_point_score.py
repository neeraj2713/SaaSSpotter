"""Demand score history schemas (Phase 5 foundation)."""

from datetime import datetime

from pydantic import Field

from app.models.common import MongoModel, utc_now


class PainPointScoreCreate(MongoModel):
    pain_point_id: str
    demand_score: int = Field(ge=1, le=10)
    recorded_at: datetime = Field(default_factory=utc_now)


class PainPointScoreRead(PainPointScoreCreate):
    id: str = Field(alias="_id")
