"""
Pipeline orchestration: scrape Reddit posts and process them through AI.

Designed for Step Functions — scrape_stage returns post IDs for Map fan-out;
process_post_stage handles a single post.
"""

import logging

from app.core.config import Settings
from app.db.mongodb import get_database
from app.db.repositories.pain_points import PainPointRepository
from app.db.repositories.raw_posts import RawPostRepository
from app.models.common import ProcessResult, ScrapeResult
from app.models.pain_point import PainPointCreate
from app.services.ai_service import AIService
from app.services.scraper_service import ScraperService

logger = logging.getLogger(__name__)


class PipelineService:
    """Orchestrates the scrape → filter → generate pipeline."""

    def __init__(self, settings: Settings | None = None):
        from app.core.config import get_settings

        self._settings = settings or get_settings()
        db = get_database()
        self._raw_posts = RawPostRepository(db)
        self._pain_points = PainPointRepository(db)
        self._scraper = ScraperService(self._settings)
        self._ai = AIService(self._settings)

    def scrape_stage(self) -> ScrapeResult:
        """
        Scrape Reddit and persist raw posts.

        Returns IDs of posts that still need AI processing.
        """
        posts = self._scraper.scrape_web()
        inserted = self._raw_posts.upsert_many(posts)
        unprocessed = self._raw_posts.find_unprocessed()
        ids = [p.id for p in unprocessed]

        logger.info(
            "Scrape stage complete: scraped=%d inserted=%d to_process=%d",
            len(posts),
            inserted,
            len(ids),
        )
        return ScrapeResult(scraped_count=len(posts), unprocessed_ids=ids)

    def process_post_stage(self, raw_post_id: str) -> ProcessResult:
        """
        Filter and generate ideas for a single raw post.

        Idempotent — skips already-processed posts.
        """
        post = self._raw_posts.find_by_id(raw_post_id)
        if post is None:
            return ProcessResult(
                raw_post_id=raw_post_id,
                processed=False,
                skipped_reason="post_not_found",
            )

        if post.processed_at is not None:
            return ProcessResult(
                raw_post_id=raw_post_id,
                processed=True,
                skipped_reason="already_processed",
            )

        try:
            filter_result = self._ai.filter_pain_point(post.text, post.subreddit)
            if not filter_result.is_valid:
                self._raw_posts.mark_processed(raw_post_id)
                return ProcessResult(
                    raw_post_id=raw_post_id,
                    processed=True,
                    is_valid_pain_point=False,
                    skipped_reason=filter_result.reason or "not_valid",
                )

            ideas = self._ai.generate_ideas(post.text, post.subreddit)
            pain_point = PainPointCreate(
                original_post_id=raw_post_id,
                core_problem=ideas.core_problem,
                saas_idea_1=ideas.saas_idea_1,
                saas_idea_2=ideas.saas_idea_2,
                demand_score=ideas.demand_score,
                industry_tag=ideas.industry_tag,
                source_url=post.url,
            )
            pain_point_id = self._pain_points.insert_one(pain_point)
            self._raw_posts.mark_processed(raw_post_id)

            return ProcessResult(
                raw_post_id=raw_post_id,
                processed=True,
                is_valid_pain_point=True,
                pain_point_id=pain_point_id,
            )
        except Exception as exc:
            logger.exception("Failed to process post %s", raw_post_id)
            return ProcessResult(
                raw_post_id=raw_post_id,
                processed=False,
                skipped_reason=str(exc),
            )

    def run_local_pipeline(self) -> dict:
        """Run full pipeline inline for local development."""
        scrape = self.scrape_stage()
        results = []
        for post_id in scrape.unprocessed_ids:
            results.append(self.process_post_stage(post_id).model_dump())
        return {
            "scraped_count": scrape.scraped_count,
            "processed_count": len(results),
            "results": results,
        }
