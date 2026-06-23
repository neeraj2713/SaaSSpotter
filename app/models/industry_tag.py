"""Industry tag aggregation schemas."""

from pydantic import BaseModel


class IndustryTagCount(BaseModel):
    tag: str
    count: int


class IndustryTagsResponse(BaseModel):
    tags: list[IndustryTagCount]
