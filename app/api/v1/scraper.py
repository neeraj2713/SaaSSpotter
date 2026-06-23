"""Scraper trigger endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from app.api.deps import get_app_settings, get_pipeline_service
from app.aws.stepfunctions import describe_execution, start_pipeline_execution
from app.core.config import Settings
from app.core.exceptions import AppError
from app.services.pipeline_service import PipelineService

router = APIRouter(tags=["scraper"])


def _verify_admin_key(
    settings: Settings = Depends(get_app_settings),
    x_admin_key: str | None = Header(default=None),
) -> None:
    if settings.admin_api_key and x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key")


@router.post("/trigger-scrape", status_code=202, include_in_schema=True)
def trigger_scrape(
    settings: Settings = Depends(get_app_settings),
    pipeline: PipelineService = Depends(get_pipeline_service),
    _: None = Depends(_verify_admin_key),
):
    """
    Manually trigger the scraping pipeline.

    In production, starts a Step Functions execution.
    With LOCAL_PIPELINE_MODE=true, runs the pipeline inline.
    """
    if settings.local_pipeline_mode:
        result = pipeline.run_local_pipeline()
        return JSONResponse(
            status_code=202,
            content={"status": "completed", "mode": "local", **result},
        )

    try:
        execution_arn = start_pipeline_execution(
            name=f"painpoint-manual-{uuid4().hex[:12]}"
        )
        return JSONResponse(
            status_code=202,
            content={"status": "started", "execution_arn": execution_arn},
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/scrape-status/{execution_arn:path}")
def scrape_status(execution_arn: str):
    """Poll Step Functions execution status."""
    try:
        return describe_execution(execution_arn)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
