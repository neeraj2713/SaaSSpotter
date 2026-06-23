"""Data access for demand score history (Phase 5 foundation)."""

from typing import List

from pymongo.database import Database

from app.models.pain_point_score import PainPointScoreCreate, PainPointScoreRead


class PainPointScoreRepository:
    def __init__(self, db: Database):
        self._collection = db.pain_point_scores

    def insert_one(self, score: PainPointScoreCreate) -> str:
        result = self._collection.insert_one(score.model_dump())
        return str(result.inserted_id)

    def find_by_pain_point_id(
        self,
        pain_point_id: str,
        limit: int = 30,
    ) -> List[PainPointScoreRead]:
        cursor = (
            self._collection.find({"pain_point_id": pain_point_id})
            .sort("recorded_at", 1)
            .limit(limit)
        )
        items: list[PainPointScoreRead] = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(PainPointScoreRead.model_validate(doc))
        return items
