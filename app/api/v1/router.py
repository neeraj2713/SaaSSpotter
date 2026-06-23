"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import clusters, digest, industry_tags, painpoints, scraper, stats, user

router = APIRouter()
router.include_router(painpoints.router)
router.include_router(industry_tags.router)
router.include_router(clusters.router)
router.include_router(digest.router)
router.include_router(stats.router)
router.include_router(user.router)
router.include_router(scraper.router)
