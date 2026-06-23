"""Lambda entry point for Step Functions ProcessPost Map iteration."""

import logging

from app.aws.secrets import init_settings_from_secrets
from app.db.mongodb import ensure_indexes
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def handler(event, context):
    """
    Process a single raw post through Gemini filter + idea generation.

    Input: { "raw_post_id": "<mongodb_id>" }
    """
    init_settings_from_secrets()
    ensure_indexes()

    raw_post_id = event.get("raw_post_id")
    if not raw_post_id:
        raise ValueError("raw_post_id is required")

    pipeline = PipelineService()
    result = pipeline.process_post_stage(raw_post_id)
    return result.model_dump()
