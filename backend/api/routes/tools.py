"""The two endpoints every client uses (desktop RemoteRunner and the PWA):

    GET  /api/tools          -> [ToolInfo, ...]
    POST /api/tools/{name}   multipart: file=<image>, params=<JSON string>, format=png|jpeg|webp
                             -> the result image, or {"detail": "message"} with a 4xx/5xx status
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from api.dependencies import get_engine, get_service, require_auth
from engine.engine import Engine
from engine.errors import EngineError, ModelUnavailable, ParamError, ToolNotFound
from services.image_service import ImageService

log = logging.getLogger("image_studio")
router = APIRouter(prefix="/tools", tags=["tools"], dependencies=[Depends(require_auth)])


@router.get("")
def list_tools(engine: Engine = Depends(get_engine)) -> list[dict[str, Any]]:
    return [info.to_dict() for info in engine.describe_tools()]


def _parse_params(raw: str) -> dict[str, Any]:
    try:
        params = json.loads(raw or "{}")
    except json.JSONDecodeError:
        raise HTTPException(400, "params must be valid JSON") from None
    if not isinstance(params, dict):
        raise HTTPException(400, "params must be a JSON object")
    return params


@router.post("/{name}")
def run_tool(
    name: str,
    file: UploadFile = File(...),
    params: str = Form("{}"),
    format: str = Form("png"),
    engine: Engine = Depends(get_engine),
    service: ImageService = Depends(get_service),
) -> Response:
    try:
        engine.registry.get(name)                      # unknown tool: fail before decoding anything
    except ToolNotFound as exc:
        raise HTTPException(404, str(exc)) from None

    options = _parse_params(params)
    image = service.decode(service.read_upload(file.file))

    started = time.perf_counter()
    try:
        result = service.run(name, image, options)
    except ParamError as exc:
        raise HTTPException(422, str(exc)) from None
    except ModelUnavailable as exc:
        raise HTTPException(503, str(exc)) from None
    except EngineError as exc:
        raise HTTPException(400, str(exc)) from None
    except HTTPException:
        raise
    except Exception:                                  # noqa: BLE001 - never leak internals to clients
        log.exception("Tool '%s' crashed", name)
        raise HTTPException(500, "Processing failed unexpectedly") from None

    content, media_type = service.encode(result, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "X-Image-Width": str(result.width),
            "X-Image-Height": str(result.height),
            "X-Process-Ms": str(round((time.perf_counter() - started) * 1000)),
            "Cache-Control": "no-store",
        },
    )
