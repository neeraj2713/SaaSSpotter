"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import painpoints, scraper

router = APIRouter()
router.include_router(painpoints.router)
router.include_router(scraper.router)
