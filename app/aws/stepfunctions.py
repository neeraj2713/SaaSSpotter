"""AWS Step Functions helpers for starting and inspecting pipeline executions."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import AppError, ServiceUnavailableError

logger = logging.getLogger(__name__)


def _client():
    return boto3.client("stepfunctions", region_name=settings.aws_region)


def start_pipeline_execution(
    *,
    name: str | None = None,
    input_payload: dict[str, Any] | None = None,
) -> str:
    """
    Start the PainPoint.io scrape pipeline state machine.

    Returns the execution ARN.
    """
    state_machine_arn = settings.step_functions_state_machine_arn
    if not state_machine_arn:
        raise ServiceUnavailableError(
            "STEP_FUNCTIONS_STATE_MACHINE_ARN is not configured"
        )

    execution_name = name or f"painpoint-manual-{uuid4().hex[:12]}"
    try:
        response = _client().start_execution(
            stateMachineArn=state_machine_arn,
            name=execution_name,
            input=json_dumps(input_payload or {}),
        )
        execution_arn: str = response["executionArn"]
        logger.info("Started pipeline execution: %s", execution_arn)
        return execution_arn
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "ExecutionAlreadyExists":
            raise AppError(
                "A pipeline execution with this name is already running",
                status_code=409,
            ) from exc
        logger.exception("Failed to start Step Functions execution")
        raise ServiceUnavailableError("Failed to start pipeline execution") from exc


def start_daily_pipeline_execution() -> str:
    """Start a daily pipeline execution with a date-based name for deduplication."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return start_pipeline_execution(name=f"painpoint-{today}")


def describe_execution(execution_arn: str) -> dict[str, Any]:
    """Return Step Functions execution status for polling."""
    try:
        response = _client().describe_execution(executionArn=execution_arn)
        return {
            "execution_arn": response["executionArn"],
            "status": response["status"],
            "start_date": response.get("startDate"),
            "stop_date": response.get("stopDate"),
        }
    except ClientError as exc:
        logger.exception("Failed to describe execution: %s", execution_arn)
        raise ServiceUnavailableError("Failed to fetch execution status") from exc


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload)
