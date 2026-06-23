"""Data access for platform meta documents."""

from datetime import datetime

from pymongo.database import Database

from app.models.common import utc_now


class MetaRepository:
    _DOC_ID = "platform"

    def __init__(self, db: Database):
        self._collection = db.meta

    def set_last_scrape_at(self, when: datetime | None = None) -> None:
        timestamp = when or utc_now()
        self._collection.update_one(
            {"_id": self._DOC_ID},
            {"$set": {"last_scrape_at": timestamp}},
            upsert=True,
        )

    def get_last_scrape_at(self) -> datetime | None:
        doc = self._collection.find_one({"_id": self._DOC_ID})
        if doc is None:
            return None
        return doc.get("last_scrape_at")
