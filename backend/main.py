"""Image Tools Studio API.

Run from this folder:   uvicorn main:app --reload --port 8000
Interactive docs:       http://localhost:8000/docs

The API contains no image-processing code. It accepts uploads, validates them and calls the
same engine.run() that the desktop app uses, so a tool is written once and works everywhere.
"""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

try:
    import engine  # noqa: F401  (installed: Docker, or `pip install -e DesktopApp`)
except ImportError:  # plain checkout: use the DesktopApp folder next to this one
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "DesktopApp"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, tools
from engine.engine import Engine
from services.image_service import ImageService
from settings import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine_ = Engine(weights_dir=settings.weights_dir, device=settings.device)
        app.state.settings = settings
        app.state.engine = engine_
        app.state.service = ImageService(engine_, settings)
        yield
        engine_.models.unload()

    app = FastAPI(title="Image Tools Studio API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Image-Width", "X-Image-Height", "X-Process-Ms"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(tools.router, prefix="/api")
    return app


app = create_app()
