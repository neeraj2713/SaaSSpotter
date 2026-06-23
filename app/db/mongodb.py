"""MongoDB connection with module-level client reuse for Lambda warm starts."""

import logging

from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongodb_uri,
            maxPoolSize=1,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        logger.info("MongoDB client initialized")
    return _client


def get_database() -> Database:
    return get_client()[settings.mongodb_db_name]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed")


def ensure_indexes() -> None:
    db = get_database()
    db.raw_posts.create_index("source_id", unique=True)
    db.raw_posts.create_index("processed_at")
    db.pain_points.create_index([("created_at", -1)])
    db.pain_points.create_index("original_post_id", unique=True)
    logger.info("MongoDB indexes ensured")
