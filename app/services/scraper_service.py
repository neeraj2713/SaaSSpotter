"""
Reddit scraping service using praw.

Fetches posts from configured subreddits matching complaint-based keywords.
"""

import logging
from datetime import datetime, timezone
from typing import List, Set

import praw

from app.core.config import Settings
from app.models.raw_post import RawPostCreate

logger = logging.getLogger(__name__)


class ScraperService:
    """Extracts candidate pain-point posts from Reddit."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._reddit: praw.Reddit | None = None

    def _get_reddit(self) -> praw.Reddit:
        if self._reddit is None:
            if not self._settings.reddit_client_id or not self._settings.reddit_client_secret:
                raise ValueError("Reddit API credentials are not configured")
            self._reddit = praw.Reddit(
                client_id=self._settings.reddit_client_id,
                client_secret=self._settings.reddit_client_secret,
                user_agent=self._settings.reddit_user_agent,
            )
        return self._reddit

    def scrape_subreddits(self) -> List[RawPostCreate]:
        """
        Search target subreddits for posts matching complaint keywords.

        Returns deduplicated RawPostCreate objects (by source_id).
        """
        reddit = self._get_reddit()
        seen_ids: Set[str] = set()
        posts: List[RawPostCreate] = []
        limit_per_query = max(5, self._settings.scrape_post_limit // max(
            len(self._settings.subreddit_list) * len(self._settings.keyword_list), 1
        ))

        for subreddit_name in self._settings.subreddit_list:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for keyword in self._settings.keyword_list:
                    for submission in subreddit.search(
                        keyword, sort="new", time_filter="week", limit=limit_per_query
                    ):
                        post = self._submission_to_post(submission, subreddit_name)
                        if post and post.source_id not in seen_ids:
                            seen_ids.add(post.source_id)
                            posts.append(post)
                            if len(posts) >= self._settings.scrape_post_limit:
                                return posts
            except Exception:
                logger.exception("Failed to scrape subreddit: %s", subreddit_name)
                continue

        logger.info("Scraped %d posts from Reddit", len(posts))
        return posts

    def _submission_to_post(self, submission, subreddit_name: str) -> RawPostCreate | None:
        if submission.stickied or submission.removed_by_category:
            return None

        title = (submission.title or "").strip()
        body = (submission.selftext or "").strip()
        text = f"{title}\n\n{body}".strip() if body else title

        if len(text) < 20:
            return None

        created_at = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
        url = f"https://reddit.com{submission.permalink}"

        return RawPostCreate(
            source="reddit",
            source_id=submission.id,
            text=text,
            url=url,
            subreddit=subreddit_name,
            created_at=created_at,
        )
