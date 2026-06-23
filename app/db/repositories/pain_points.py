"""Data access for pain_points collection."""

import re
from datetime import datetime, timedelta
from typing import List, Literal, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database

from app.models.cluster import ClusterCount
from app.models.industry_tag import IndustryTagCount
from app.models.pain_point import PainPointCreate, PainPointRead

SortField = Literal["created_at", "demand_score"]
SortOrder = Literal["asc", "desc"]

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "that",
        "this",
        "these",
        "those",
        "it",
        "its",
        "they",
        "them",
        "their",
        "we",
        "our",
        "you",
        "your",
        "i",
        "my",
        "me",
        "not",
        "no",
        "so",
        "if",
        "as",
        "up",
        "out",
        "about",
        "into",
        "over",
        "after",
        "before",
        "between",
        "through",
        "during",
        "without",
        "within",
        "along",
        "than",
        "too",
        "very",
        "just",
        "also",
        "more",
        "most",
        "other",
        "some",
        "such",
        "only",
        "own",
        "same",
        "than",
        "then",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "many",
        "much",
        "any",
        "who",
        "whom",
        "which",
        "what",
        "while",
        "because",
        "until",
        "although",
        "though",
        "even",
        "still",
        "already",
        "yet",
        "again",
        "once",
        "here",
        "now",
        "get",
        "got",
        "like",
        "make",
        "made",
        "use",
        "using",
        "used",
        "want",
        "way",
        "new",
        "one",
        "two",
        "really",
        "well",
        "back",
        "even",
        "still",
        "going",
        "goes",
        "went",
        "come",
        "came",
        "know",
        "think",
        "see",
        "look",
        "looking",
        "try",
        "trying",
        "work",
        "working",
        "help",
        "helps",
        "issue",
        "issues",
        "problem",
        "problems",
    }
)


def _sanitize_search_query(q: str | None) -> str | None:
    if not q:
        return None
    cleaned = q.strip()
    if len(cleaned) < 2:
        return None
    return cleaned[:200]


def _extract_keywords(text: str, limit: int = 5) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    keywords: list[str] = []
    for token in tokens:
        if len(token) < 3 or token in _STOPWORDS:
            continue
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= limit:
            break
    return keywords


class PainPointRepository:
    def __init__(self, db: Database):
        self._collection = db.pain_points

    def insert_one(self, pain_point: PainPointCreate) -> str:
        result = self._collection.insert_one(pain_point.model_dump())
        return str(result.inserted_id)

    def count_all(self) -> int:
        return self._collection.count_documents({})

    def find_by_id(self, pain_point_id: str) -> PainPointRead | None:
        try:
            oid = ObjectId(pain_point_id)
        except (InvalidId, TypeError):
            return None
        doc = self._collection.find_one({"_id": oid})
        if doc is None:
            return None
        return self._to_read(doc)

    def find_by_ids(self, pain_point_ids: list[str]) -> list[PainPointRead]:
        oids: list[ObjectId] = []
        for pain_point_id in pain_point_ids:
            try:
                oids.append(ObjectId(pain_point_id))
            except (InvalidId, TypeError):
                continue
        if not oids:
            return []
        cursor = self._collection.find({"_id": {"$in": oids}})
        items = {str(doc["_id"]): self._to_read(doc) for doc in cursor}
        return [items[pid] for pid in pain_point_ids if pid in items]

    def count_since(self, since: datetime) -> int:
        return self._collection.count_documents({"created_at": {"$gte": since}})

    def find_top_by_demand(self, limit: int = 5, since: datetime | None = None) -> list[PainPointRead]:
        query: dict = {}
        if since:
            query["created_at"] = {"$gte": since}
        cursor = self._collection.find(query).sort("demand_score", -1).limit(limit)
        return [self._to_read(doc) for doc in cursor]

    def find_trending(self, limit: int = 5) -> list[PainPointRead]:
        cutoff = datetime.utcnow() - timedelta(days=7)
        cursor = (
            self._collection.find(
                {"created_at": {"$gte": cutoff}, "demand_score": {"$gte": 7}}
            )
            .sort("demand_score", -1)
            .limit(limit)
        )
        return [self._to_read(doc) for doc in cursor]

    def find_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        industry_tag: Optional[str] = None,
        cluster_slug: Optional[str] = None,
        q: Optional[str] = None,
        sort: SortField = "created_at",
        order: SortOrder = "desc",
        trending: bool = False,
        since: Optional[datetime] = None,
    ) -> Tuple[List[PainPointRead], int]:
        query: dict = {}
        if industry_tag:
            query["$or"] = [
                {"industry_tag": industry_tag},
                {"industry_tags": industry_tag},
            ]
        if cluster_slug:
            query["cluster_slug"] = cluster_slug

        search_q = _sanitize_search_query(q)
        use_text_search = search_q is not None
        if use_text_search:
            query["$text"] = {"$search": search_q}

        if trending:
            cutoff = datetime.utcnow() - timedelta(days=7)
            query["created_at"] = {"$gte": cutoff}
            query["demand_score"] = {"$gte": 7}
        elif since:
            query["created_at"] = {"$gte": since}

        total = self._collection.count_documents(query)
        skip = (page - 1) * page_size

        sort_direction = -1 if order == "desc" else 1
        if use_text_search and sort == "created_at":
            sort_spec = [("score", {"$meta": "textScore"})]
            projection = {"score": {"$meta": "textScore"}}
        else:
            sort_spec = [(sort, sort_direction)]
            projection = None

        cursor = self._collection.find(query, projection)
        cursor = cursor.sort(sort_spec).skip(skip).limit(page_size)
        items = [self._to_read(doc) for doc in cursor]
        return items, total

    def aggregate_industry_tags(self) -> list[IndustryTagCount]:
        pipeline = [
            {
                "$project": {
                    "tags": {
                        "$setUnion": [
                            {
                                "$cond": [
                                    {"$isArray": "$industry_tags"},
                                    "$industry_tags",
                                    [],
                                ]
                            },
                            ["$industry_tag"],
                        ]
                    }
                }
            },
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$project": {"_id": 0, "tag": "$_id", "count": 1}},
        ]
        return [
            IndustryTagCount.model_validate(doc)
            for doc in self._collection.aggregate(pipeline)
        ]

    def aggregate_clusters(self, limit: int = 20) -> list[ClusterCount]:
        pipeline = [
            {"$match": {"cluster_slug": {"$nin": [None, ""]}}},
            {
                "$group": {
                    "_id": "$cluster_slug",
                    "label": {"$first": "$cluster_label"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "slug": "$_id",
                    "label": {"$ifNull": ["$label", "$_id"]},
                    "count": 1,
                }
            },
        ]
        return [ClusterCount.model_validate(doc) for doc in self._collection.aggregate(pipeline)]

    def find_similar(
        self,
        pain_point_id: str,
        limit: int = 5,
    ) -> list[PainPointRead]:
        source = self.find_by_id(pain_point_id)
        if source is None:
            return []

        try:
            source_oid = ObjectId(pain_point_id)
        except (InvalidId, TypeError):
            return []

        seen_ids = {source_oid}
        results: list[PainPointRead] = []

        tag_cursor = (
            self._collection.find(
                {
                    "$or": [
                        {"industry_tag": source.industry_tag},
                        {"industry_tags": source.industry_tag},
                    ],
                    "_id": {"$ne": source_oid},
                }
            )
            .sort("demand_score", -1)
            .limit(limit)
        )
        for doc in tag_cursor:
            seen_ids.add(doc["_id"])
            results.append(self._to_read(doc))

        if len(results) >= limit:
            return results[:limit]

        keywords = _extract_keywords(source.core_problem)
        if keywords:
            search_text = " ".join(keywords)
            text_cursor = (
                self._collection.find(
                    {
                        "$text": {"$search": search_text},
                        "_id": {"$nin": list(seen_ids)},
                    },
                    {"score": {"$meta": "textScore"}},
                )
                .sort([("score", {"$meta": "textScore"})])
                .limit(limit - len(results))
            )
            for doc in text_cursor:
                seen_ids.add(doc["_id"])
                results.append(self._to_read(doc))

        return results[:limit]

    def _to_read(self, doc: dict) -> PainPointRead:
        doc = dict(doc)
        doc.pop("score", None)
        doc["_id"] = str(doc["_id"])
        return PainPointRead.model_validate(doc)
