#!/usr/bin/env python3
"""Rule-based backfill for industry tags and clusters on existing pain points."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.constants.industry_taxonomy import normalize_industry_tags, split_raw_tags
from app.db.mongodb import close_client, ensure_indexes, get_database


def _slugify_cluster(text: str) -> str:
    words = split_raw_tags(text.replace(" ", "-"))
    if not words:
        return "general"
    return "-".join(words[0].split()[:4]).lower()[:40] or "general"


def main() -> int:
    db = get_database()
    ensure_indexes()
    updated = 0

    for doc in db.pain_points.find({}):
        raw_tag = doc.get("industry_tag", "other")
        extras = doc.get("industry_tags") or []
        primary, secondary = normalize_industry_tags(raw_tag, extras)

        cluster_slug = doc.get("cluster_slug")
        cluster_label = doc.get("cluster_label")
        if not cluster_slug:
            cluster_slug = _slugify_cluster(doc.get("core_problem", "general"))
            cluster_label = doc.get("core_problem", "General")[:60]

        db.pain_points.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "industry_tag": primary,
                    "industry_tags": secondary,
                    "cluster_slug": cluster_slug,
                    "cluster_label": cluster_label,
                }
            },
        )
        updated += 1

    print(f"Backfilled {updated} pain points")
    close_client()
    return 0


if __name__ == "__main__":
    sys.exit(main())
