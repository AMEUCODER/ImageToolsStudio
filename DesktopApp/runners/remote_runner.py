"""Runs tools on the FastAPI backend. Same interface as LocalRunner.

Backend contract (to implement in backend/):
    GET  /api/tools            -> [ToolInfo.to_dict(), ...]
    POST /api/tools/{name}     multipart: file=<image>, params=<json string>
                               -> 200 with the result image bytes (PNG)
                               -> 4xx/5xx with {"detail": "message"}
Auth: "Authorization: Bearer <token>" when a token is configured.
"""
from __future__ import annotations

import json
from typing import Any

from PIL import Image

from engine.image_exporter import image_to_bytes
from engine.image_loader import image_from_bytes
from engine.schemas.responses import ToolInfo
from runners.base_runner import BaseRunner, RunnerError


class RemoteRunner(BaseRunner):
    def __init__(self, server_url: str, token: str = "", timeout: float = 300):
        self.base = server_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @staticmethod
    def _requests():
        try:
            import requests
        except ImportError as exc:
            raise RunnerError("Remote mode needs requests: pip install requests") from exc
        return requests

    @staticmethod
    def _error_text(response) -> str:
        try:
            return str(response.json().get("detail", response.text))
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

    def describe_tools(self) -> list[ToolInfo]:
        requests = self._requests()
        try:
            response = requests.get(f"{self.base}/api/tools", headers=self._headers(), timeout=15)
        except requests.RequestException as exc:
            raise RunnerError(f"Cannot reach server at {self.base}: {exc}") from exc
        if not response.ok:
            raise RunnerError(self._error_text(response))
        return [ToolInfo.from_dict(item) for item in response.json()]

    def run(self, tool: str, image: Image.Image, params: dict[str, Any] | None = None) -> Image.Image:
        requests = self._requests()
        try:
            response = requests.post(
                f"{self.base}/api/tools/{tool}",
                headers=self._headers(),
                files={"file": ("image.png", image_to_bytes(image, "PNG"), "image/png")},
                data={"params": json.dumps(params or {})},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise RunnerError(f"Cannot reach server at {self.base}: {exc}") from exc
        if not response.ok:
            raise RunnerError(self._error_text(response))
        return image_from_bytes(response.content)
