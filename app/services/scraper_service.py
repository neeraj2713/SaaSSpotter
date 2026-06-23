"""
Web scraping service using Firecrawl.

Searches the web for complaint-style content and scrapes full page markdown.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, List, Set

from firecrawl import Firecrawl

from app.core.config import Settings
from app.models.common import utc_now
from app.models.raw_post import RawPostCreate

logger = logging.getLogger(__name__)


class ScraperService:
    """Extracts candidate pain-point posts from the web via Firecrawl search."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: Firecrawl | None = None

    def _get_client(self) -> Firecrawl:
        if self._client is None:
            if not self._settings.firecrawl_api_key:
                raise ValueError("FIRECRAWL_API_KEY is not configured")
            self._client = Firecrawl(api_key=self._settings.firecrawl_api_key)
        return self._client

    def scrape_web(self) -> List[RawPostCreate]:
        """
        Search configured targets × keywords via Firecrawl and scrape results.

        Returns deduplicated RawPostCreate objects (by source_id / URL hash).
        """
        client = self._get_client()
        seen_ids: Set[str] = set()
        posts: List[RawPostCreate] = []

        target_count = max(len(self._settings.scrape_target_list), 1)
        keyword_count = max(len(self._settings.keyword_list), 1)
        limit_per_query = max(
            3,
            self._settings.scrape_post_limit // (target_count * keyword_count),
        )

        for target in self._settings.scrape_target_list:
            for keyword in self._settings.keyword_list:
                query = self._build_search_query(target, keyword)
                try:
                    results = client.search(
                        query,
                        limit=limit_per_query,
                        scrape_options={"formats": ["markdown"]},
                    )
                    for item in self._iter_web_results(results):
                        post = self._result_to_post(item, target)
                        if post and post.source_id not in seen_ids:
                            seen_ids.add(post.source_id)
                            posts.append(post)
                            if len(posts) >= self._settings.scrape_post_limit:
                                return posts
                except Exception:
                    logger.exception(
                        "Firecrawl search failed for target=%s keyword=%s",
                        target,
                        keyword,
                    )
                    continue

        logger.info("Scraped %d posts via Firecrawl", len(posts))
        return posts

    def scrape_subreddits(self) -> List[RawPostCreate]:
        """Backward-compatible alias for pipeline callers."""
        return self.scrape_web()

    def _build_search_query(self, target: str, keyword: str) -> str:
        target = target.strip()
        if target.startswith("site:"):
            return f"{target} {keyword}"
        return f"site:{target} {keyword}"

    def _iter_web_results(self, results: Any) -> List[Any]:
        if results is None:
            return []
        if isinstance(results, dict):
            data = results.get("data", results)
            if isinstance(data, dict):
                return list(data.get("web") or [])
            if isinstance(data, list):
                return data
            return list(results.get("web") or [])
        web = getattr(results, "web", None)
        if web is not None:
            return list(web)
        data = getattr(results, "data", None)
        if isinstance(data, list):
            return data
        return []

    def _result_to_post(self, item: Any, target: str) -> RawPostCreate | None:
        url = self._get_field(item, "url")
        if not url:
            return None

        title = (self._get_field(item, "title") or "").strip()
        description = (self._get_field(item, "description") or "").strip()
        markdown = (self._get_field(item, "markdown") or "").strip()

        if markdown:
            text = f"{title}\n\n{markdown}".strip() if title else markdown
        elif title and description:
            text = f"{title}\n\n{description}".strip()
        else:
            text = title or description

        if len(text) < 20:
            return None

        source_id = hashlib.sha256(url.encode()).hexdigest()[:32]
        created_at = self._parse_created_at(item) or utc_now()
        source_tag = target.replace("site:", "").split("/")[-1] or target

        return RawPostCreate(
            source="firecrawl",
            source_id=source_id,
            text=text[:20000],
            url=url,
            subreddit=source_tag,
            created_at=created_at,
        )

    def _get_field(self, item: Any, key: str) -> str | None:
        if isinstance(item, dict):
            value = item.get(key)
        else:
            value = getattr(item, key, None)
        return str(value) if value is not None else None

    def _parse_created_at(self, item: Any) -> datetime | None:
        if isinstance(item, dict):
            meta = item.get("metadata")
        else:
            meta = getattr(item, "metadata", None)

        if not isinstance(meta, dict):
            return None

        for key in ("publishedTime", "modifiedTime", "date"):
            raw = meta.get(key)
            if not raw:
                continue
            try:
                parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
        return None
