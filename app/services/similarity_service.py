"""Vector search foundation for similar ideas (Phase 5).

Atlas Vector Search requires an embedding field on pain_points documents
and a vector search index configured in MongoDB Atlas. The MVP similar-ideas
endpoint uses industry_tag + keyword overlap; swap find_similar implementation
here when embeddings are available.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.repositories.pain_points import PainPointRepository
    from app.models.pain_point import PainPointRead


def find_similar_by_embedding(
    repo: "PainPointRepository",
    pain_point_id: str,
    limit: int = 5,
) -> list["PainPointRead"]:
    """Placeholder for Atlas Vector Search integration."""
    raise NotImplementedError(
        "Vector search requires pain_points.embedding and an Atlas vector index"
    )
