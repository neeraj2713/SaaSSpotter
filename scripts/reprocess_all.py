#!/usr/bin/env python3
"""Clear generated ideas and re-run the AI pipeline on all raw posts."""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.mongodb import close_client, ensure_indexes, get_database
from app.services.pipeline_service import PipelineService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    db = get_database()
    ensure_indexes()

    pain_points_deleted = db.pain_points.delete_many({}).deleted_count
    scores_deleted = db.pain_point_scores.delete_many({}).deleted_count
    raw_reset = db.raw_posts.update_many({}, {"$set": {"processed_at": None}}).modified_count
    raw_total = db.raw_posts.count_documents({})

    logger.info(
        "Reset complete: pain_points=%d scores=%d raw_posts_reset=%d raw_posts_total=%d",
        pain_points_deleted,
        scores_deleted,
        raw_reset,
        raw_total,
    )

    if raw_total == 0:
        logger.info("No raw posts found — running scrape first")
        pipeline = PipelineService()
        scrape = pipeline.scrape_stage()
        logger.info("Scraped %d posts", scrape.scraped_count)

    pipeline = PipelineService()
    result = pipeline.run_local_pipeline()

    summary = {
        "pain_points_deleted": pain_points_deleted,
        "scores_deleted": scores_deleted,
        "raw_posts_reset": raw_reset,
        "scraped_count": result.get("scraped_count", 0),
        "processed_count": result.get("processed_count", 0),
        "valid_pain_points": sum(
            1
            for r in result.get("results", [])
            if r.get("is_valid_pain_point")
        ),
    }
    print(json.dumps(summary, indent=2))
    close_client()
    return 0


if __name__ == "__main__":
    sys.exit(main())
