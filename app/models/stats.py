"""Platform stats schemas."""

from datetime import datetime

from pydantic import BaseModel


class StatsResponse(BaseModel):
    last_scrape_at: datetime | None = None
    total_pain_points: int = 0
