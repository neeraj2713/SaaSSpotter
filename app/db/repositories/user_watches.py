"""Data access for user alert watches."""

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

from app.models.user import AlertWatchCreate, AlertWatchRead


class UserWatchesRepository:
    def __init__(self, db: Database):
        self._collection = db.user_alert_watches

    def list_watches(self, user_id: str) -> list[AlertWatchRead]:
        cursor = self._collection.find({"user_id": user_id}).sort("created_at", -1)
        items: list[AlertWatchRead] = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(AlertWatchRead.model_validate(doc))
        return items

    def create_watch(self, user_id: str, watch: AlertWatchCreate) -> AlertWatchRead:
        doc = {
            "user_id": user_id,
            "keywords": watch.keywords[:10],
            "tags": watch.tags[:10],
            "label": watch.label,
        }
        result = self._collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return AlertWatchRead.model_validate(doc)

    def delete_watch(self, user_id: str, watch_id: str) -> bool:
        try:
            oid = ObjectId(watch_id)
        except (InvalidId, TypeError):
            return False
        result = self._collection.delete_one({"_id": oid, "user_id": user_id})
        return result.deleted_count > 0
