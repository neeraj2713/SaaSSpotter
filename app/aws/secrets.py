"""Load application secrets from AWS Secrets Manager or return empty dict for local dev."""

import json
import logging
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

_secrets_cache: dict[str, str] | None = None


def load_secrets() -> dict[str, str]:
    """
    Fetch secrets from AWS Secrets Manager when configured.

    Returns an empty dict when running locally without Secrets Manager,
    allowing pydantic-settings / .env to supply values instead.
    """
    global _secrets_cache

    if _secrets_cache is not None:
        return _secrets_cache

    secret_name = settings.aws_secrets_manager_secret_name
    if not secret_name:
        _secrets_cache = {}
        return _secrets_cache

    client = boto3.client("secretsmanager", region_name=settings.aws_region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        raw: Any = json.loads(response["SecretString"])
        if not isinstance(raw, dict):
            raise ValueError("Secret must be a JSON object")
        _secrets_cache = {str(k): str(v) for k, v in raw.items()}
        logger.info("Loaded secrets from Secrets Manager: %s", secret_name)
    except ClientError:
        logger.exception("Failed to load secrets from Secrets Manager")
        raise

    return _secrets_cache


def init_settings_from_secrets() -> None:
    """Load secrets and merge into the global settings object."""
    secrets = load_secrets()
    if secrets:
        settings.apply_secrets(secrets)


@lru_cache
def get_boto3_session():
    return boto3.Session(region_name=settings.aws_region)
