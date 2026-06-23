"""Data access for user saved ideas."""

from datetime import datetime

from pymongo.database import Database

from app.models.common import utc_now


class UserSavedRepository:
    def __init__(self, db: Database):
        self._collection = db.user_saved_ideas

    def list_ids(self, user_id: str) -> list[str]:
        cursor = self._collection.find({"user_id": user_id}).sort("saved_at", -1)
        return [doc["pain_point_id"] for doc in cursor]

    def save(self, user_id: str, pain_point_id: str) -> None:
        self._collection.update_one(
            {"user_id": user_id, "pain_point_id": pain_point_id},
            {"$set": {"user_id": user_id, "pain_point_id": pain_point_id, "saved_at": utc_now()}},
            upsert=True,
        )

    def unsave(self, user_id: str, pain_point_id: str) -> bool:
        result = self._collection.delete_one(
            {"user_id": user_id, "pain_point_id": pain_point_id}
        )
        return result.deleted_count > 0

    def is_saved(self, user_id: str, pain_point_id: str) -> bool:
        return (
            self._collection.count_documents(
                {"user_id": user_id, "pain_point_id": pain_point_id}, limit=1
            )
            > 0
        )
