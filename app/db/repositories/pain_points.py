"""Data access for pain_points collection."""

from typing import List, Optional, Tuple

from bson import ObjectId
from pymongo.database import Database

from app.models.pain_point import PainPointCreate, PainPointRead


class PainPointRepository:
    def __init__(self, db: Database):
        self._collection = db.pain_points

    def insert_one(self, pain_point: PainPointCreate) -> str:
        result = self._collection.insert_one(pain_point.model_dump())
        return str(result.inserted_id)

    def find_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        industry_tag: Optional[str] = None,
    ) -> Tuple[List[PainPointRead], int]:
        query = {}
        if industry_tag:
            query["industry_tag"] = industry_tag

        total = self._collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self._collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        items = [self._to_read(doc) for doc in cursor]
        return items, total

    def _to_read(self, doc: dict) -> PainPointRead:
        doc["_id"] = str(doc["_id"])
        return PainPointRead.model_validate(doc)
