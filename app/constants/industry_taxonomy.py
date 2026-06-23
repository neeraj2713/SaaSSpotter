"""Canonical industry tags and normalization helpers."""

from __future__ import annotations

import re

CANONICAL_INDUSTRY_TAGS: tuple[str, ...] = (
    "developer-tools",
    "marketing",
    "hr",
    "finance",
    "e-commerce",
    "freelancer-tools",
    "productivity",
    "customer-support",
    "sales",
    "legal",
    "healthcare",
    "education",
    "real-estate",
    "agency-tools",
    "ai-tools",
    "operations",
    "analytics",
    "security",
    "other",
)

_SYNONYMS: dict[str, str] = {
    "dev-tools": "developer-tools",
    "devtools": "developer-tools",
    "developer": "developer-tools",
    "engineering": "developer-tools",
    "saas": "developer-tools",
    "human-resources": "hr",
    "hr-tech": "hr",
    "recruiting": "hr",
    "fintech": "finance",
    "accounting": "finance",
    "invoicing": "finance",
    "freelance": "freelancer-tools",
    "freelancing": "freelancer-tools",
    "agency": "agency-tools",
    "collaboration": "productivity",
    "customer-service": "customer-support",
    "support": "customer-support",
    "crm": "sales",
    "ecommerce": "e-commerce",
    "retail": "e-commerce",
    "ai": "ai-tools",
    "machine-learning": "ai-tools",
    "data": "analytics",
    "bi": "analytics",
    "cybersecurity": "security",
    "compliance": "legal",
}


def _slugify(token: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", token.lower().strip())
    return cleaned.strip("-")


def _map_token(token: str) -> str:
    slug = _slugify(token)
    if not slug:
        return "other"
    if slug in CANONICAL_INDUSTRY_TAGS:
        return slug
    if slug in _SYNONYMS:
        return _SYNONYMS[slug]
    for canonical in CANONICAL_INDUSTRY_TAGS:
        if canonical in slug or slug in canonical:
            return canonical
    return "other"


def split_raw_tags(raw: str) -> list[str]:
    if not raw:
        return []
    parts = re.split(r"[,;/|]+", raw)
    return [p.strip() for p in parts if p.strip()]


def normalize_industry_tags(
    raw: str, extras: list[str] | None = None
) -> tuple[str, list[str]]:
    """Return (primary_tag, secondary_tags up to 2)."""
    tokens = split_raw_tags(raw)
    if extras:
        tokens.extend(extras)

    normalized: list[str] = []
    for token in tokens:
        mapped = _map_token(token)
        if mapped not in normalized:
            normalized.append(mapped)

    if not normalized:
        normalized = ["other"]

    primary = normalized[0]
    secondary = [tag for tag in normalized[1:3] if tag != primary]
    return primary, secondary
