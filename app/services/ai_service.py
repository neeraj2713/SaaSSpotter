"""
AI processing service using Google Gemini.

Filters raw text for genuine business pain points and generates Micro-SaaS ideas.
"""

import json
import logging

import google.generativeai as genai

from app.core.config import Settings
from app.models.common import FilterResult, IdeaResult

logger = logging.getLogger(__name__)

FILTER_PROMPT = """You are an expert at identifying genuine business and developer pain points from online posts.

Analyze the following web post from {subreddit} and determine if it describes a REAL business pain point that could inspire a Micro-SaaS product.

A valid pain point:
- Describes a specific problem, frustration, or unmet need
- Is related to business, work, productivity, or software development
- Is NOT just news, memes, self-promotion, or general discussion

Post:
{text}

Respond with JSON only:
{{"is_valid": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}"""

GENERATE_PROMPT = """You are a Micro-SaaS idea generator. Based on this pain point post, extract the core problem and generate actionable product ideas.

Post from {subreddit}:
{text}

Respond with JSON only:
{{
  "core_problem": "one sentence summary of the core problem",
  "saas_idea_1": "first actionable Micro-SaaS idea",
  "saas_idea_2": "second actionable Micro-SaaS idea",
  "demand_score": 1-10,
  "industry_tag": "kebab-case industry tag e.g. developer-tools, marketing, hr"
}}"""


class AIService:
    """Gemini-powered filter and idea generator."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._model = None

    def _get_model(self):
        if self._model is None:
            if not self._settings.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is not configured")
            genai.configure(api_key=self._settings.gemini_api_key)
            self._model = genai.GenerativeModel(
                model_name=self._settings.gemini_model,
                generation_config={"response_mime_type": "application/json"},
            )
        return self._model

    def filter_pain_point(self, text: str, subreddit: str) -> FilterResult:
        """Determine if text is a genuine business pain point."""
        prompt = FILTER_PROMPT.format(subreddit=subreddit, text=text[:4000])
        return self._call_and_parse(prompt, FilterResult)

    def generate_ideas(self, text: str, subreddit: str) -> IdeaResult:
        """Extract problem and generate two Micro-SaaS ideas."""
        prompt = GENERATE_PROMPT.format(subreddit=subreddit, text=text[:4000])
        return self._call_and_parse(prompt, IdeaResult)

    def _call_and_parse(self, prompt: str, model_class):
        model = self._get_model()
        last_error: Exception | None = None

        for attempt in range(2):
            try:
                response = model.generate_content(prompt)
                raw = response.text or "{}"
                data = json.loads(raw)
                return model_class.model_validate(data)
            except Exception as exc:
                last_error = exc
                logger.warning("Gemini parse attempt %d failed: %s", attempt + 1, exc)

        raise ValueError(f"Failed to parse Gemini response: {last_error}")
