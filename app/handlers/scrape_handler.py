"""Lambda entry point for Step Functions Scrape state."""

import logging

from app.aws.secrets import init_settings_from_secrets
from app.db.mongodb import ensure_indexes
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def handler(event, context):
    """
    Scrape Reddit and return unprocessed post IDs for Map fan-out.

    Step Functions expects: { "raw_post_ids": [...], "scraped_count": N }
    """
    init_settings_from_secrets()
    ensure_indexes()

    pipeline = PipelineService()
    result = pipeline.scrape_stage()

    return {
        "raw_post_ids": result.unprocessed_ids,
        "scraped_count": result.scraped_count,
    }
