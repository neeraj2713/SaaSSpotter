"""Clerk JWT verification for user-scoped API routes."""

from __future__ import annotations

import logging
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)


@lru_cache
def _jwks_client(issuer: str) -> PyJWKClient:
    issuer = issuer.rstrip("/")
    return PyJWKClient(f"{issuer}/.well-known/jwks.json")


def verify_clerk_token(token: str, settings: Settings) -> str:
    if not settings.clerk_issuer:
        raise HTTPException(status_code=503, detail="Authentication is not configured")

    try:
        client = _jwks_client(settings.clerk_issuer)
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer.rstrip("/"),
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        logger.warning("Clerk JWT verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return str(user_id)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing authorization token")
    return verify_clerk_token(credentials.credentials, settings)
