"""Pain cluster aggregation schemas."""

from pydantic import BaseModel


class ClusterCount(BaseModel):
    slug: str
    label: str
    count: int


class ClustersResponse(BaseModel):
    clusters: list[ClusterCount]
