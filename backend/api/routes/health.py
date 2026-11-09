"""GET /api/health: used by the frontend status light and by Docker health checks."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_engine
from engine.engine import Engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request, engine: Engine = Depends(get_engine)) -> dict:
    return {
        "status": "ok",
        "tools": len(engine.list_tools()),
        "broken_tools": sorted(engine.registry.failed),      # tools that failed to import
        "device": engine.devices.device,
        "auth_required": bool(request.app.state.settings.token),
        "max_upload_mb": request.app.state.settings.max_upload_mb,
    }
