"""Data access for user visit timestamps."""

from pymongo.database import Database

from app.models.common import utc_now


class UserVisitsRepository:
    def __init__(self, db: Database):
        self._collection = db.user_visits

    def get_last_visited(self, user_id: str):
        doc = self._collection.find_one({"user_id": user_id})
        if doc is None:
            return None
        return doc.get("last_visited_at")

    def touch(self, user_id: str):
        now = utc_now()
        self._collection.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "last_visited_at": now}},
            upsert=True,
        )
        return now
