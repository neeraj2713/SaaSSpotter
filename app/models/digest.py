"""Weekly digest schemas."""

from pydantic import BaseModel

from app.models.cluster import ClusterCount
from app.models.pain_point import PainPointRead


class DigestResponse(BaseModel):
    period_days: int
    new_count: int
    top_by_demand: list[PainPointRead]
    trending: list[PainPointRead]
    top_clusters: list[ClusterCount]
