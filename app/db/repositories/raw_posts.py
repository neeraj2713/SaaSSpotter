"""Data access for raw_posts collection."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from pymongo.database import Database

from app.models.raw_post import RawPostCreate, RawPostRead


class RawPostRepository:
    def __init__(self, db: Database):
        self._collection = db.raw_posts

    def upsert_many(self, posts: List[RawPostCreate]) -> int:
        if not posts:
            return 0
        count = 0
        for post in posts:
            result = self._collection.update_one(
                {"source_id": post.source_id},
                {"$setOnInsert": post.model_dump()},
                upsert=True,
            )
            if result.upserted_id is not None:
                count += 1
        return count

    def find_unprocessed(self, limit: int = 500) -> List[RawPostRead]:
        cursor = self._collection.find({"processed_at": None}).limit(limit)
        return [self._to_read(doc) for doc in cursor]

    def find_by_id(self, post_id: str) -> Optional[RawPostRead]:
        try:
            oid = ObjectId(post_id)
        except Exception:
            return None
        doc = self._collection.find_one({"_id": oid})
        if doc is None:
            return None
        return self._to_read(doc)

    def mark_processed(self, post_id: str) -> None:
        try:
            oid = ObjectId(post_id)
        except Exception:
            return
        self._collection.update_one(
            {"_id": oid},
            {"$set": {"processed_at": datetime.utcnow()}},
        )

    def _to_read(self, doc: dict) -> RawPostRead:
        doc["_id"] = str(doc["_id"])
        return RawPostRead.model_validate(doc)
