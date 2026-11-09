"""Shared FastAPI dependencies: the engine, the image service and optional token auth."""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, Request

from engine.engine import Engine
from services.image_service import ImageService


def get_engine(request: Request) -> Engine:
    return request.app.state.engine


def get_service(request: Request) -> ImageService:
    return request.app.state.service


def require_auth(request: Request, authorization: str | None = Header(default=None)) -> None:
    """No-op unless IMAGE_STUDIO_TOKEN is set. Then the request needs 'Authorization: Bearer <token>'."""
    expected = request.app.state.settings.token
    if not expected:
        return
    supplied = authorization[7:] if authorization and authorization.lower().startswith("bearer ") else ""
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(401, "Missing or invalid access token", headers={"WWW-Authenticate": "Bearer"})
