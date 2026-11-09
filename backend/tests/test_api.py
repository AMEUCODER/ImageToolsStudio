"""API tests. A fake-free setup: the real engine runs behind the real routes."""
import io
import json
import socket
import threading
import time

import pytest
import uvicorn
from fastapi.testclient import TestClient
from PIL import Image

from main import create_app
from settings import Settings


def make_png(size=(64, 48), color=(200, 40, 40)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "PNG")
    return buffer.getvalue()


def settings(tmp_path, **overrides) -> Settings:
    return Settings(weights_dir=tmp_path / "weights", device="cpu", **overrides)


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as c:
        yield c


def run(client, tool, params=None, data=None, headers=None, **extra):
    files = {"file": ("in.png", data if data is not None else make_png(), "image/png")}
    form = {"params": json.dumps(params or {}), **extra}
    return client.post(f"/api/tools/{tool}", files=files, data=form, headers=headers)


# ---- discovery -------------------------------------------------------------
def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["tools"] >= 2 and body["broken_tools"] == []
    assert body["auth_required"] is False


def test_tools_list_has_the_contract_the_clients_expect(client):
    tools = client.get("/api/tools").json()
    names = {t["name"] for t in tools}
    assert {"blur", "auto_enhance"} <= names
    blur = next(t for t in tools if t["name"] == "blur")
    assert {"name", "label", "description", "params"} <= set(blur)
    strength = next(p for p in blur["params"] if p["name"] == "strength")
    assert strength["kind"] == "slider" and strength["min"] == 1 and strength["max"] == 50


# ---- running tools ---------------------------------------------------------
def test_run_returns_a_png_of_the_same_size(client):
    response = run(client, "blur", {"mode": "whole", "strength": 5}, data=make_png((80, 60)))
    assert response.status_code == 200 and response.headers["content-type"] == "image/png"
    assert response.headers["x-image-width"] == "80" and response.headers["x-image-height"] == "60"
    assert Image.open(io.BytesIO(response.content)).size == (80, 60)


def test_defaults_are_filled_in(client):
    assert run(client, "auto_enhance").status_code == 200


def test_output_formats(client):
    assert run(client, "auto_enhance", format="jpeg").headers["content-type"] == "image/jpeg"
    assert run(client, "auto_enhance", format="webp").headers["content-type"] == "image/webp"
    assert run(client, "auto_enhance", format="gif").status_code == 422


def test_transparency_survives_png(client):
    rgba = io.BytesIO()
    Image.new("RGBA", (10, 10), (255, 0, 0, 90)).save(rgba, "PNG")
    out = Image.open(io.BytesIO(run(client, "auto_enhance", data=rgba.getvalue()).content))
    assert out.mode == "RGBA" and out.getpixel((0, 0))[3] == 90


# ---- errors: clear message, right status -----------------------------------
def test_unknown_tool_is_404(client):
    response = run(client, "teleport")
    assert response.status_code == 404 and "teleport" in response.json()["detail"]


def test_bad_option_is_422_with_a_readable_message(client):
    response = run(client, "blur", {"mode": "sideways"})
    assert response.status_code == 422 and "mode" in response.json()["detail"].lower()
    assert run(client, "blur", {"nope": 1}).status_code == 422


def test_params_must_be_a_json_object(client):
    files = {"file": ("in.png", make_png(), "image/png")}
    assert client.post("/api/tools/blur", files=files, data={"params": "{oops"}).status_code == 400
    assert client.post("/api/tools/blur", files=files, data={"params": "[1]"}).status_code == 400


def test_not_an_image_is_400(client):
    response = run(client, "blur", data=b"definitely not an image")
    assert response.status_code == 400 and "not a readable image" in response.json()["detail"]
    assert run(client, "blur", data=b"").status_code == 400


def test_upload_size_limit_is_413(tmp_path):
    with TestClient(create_app(settings(tmp_path, max_upload_mb=1))) as client:
        big = make_png((1500, 1500))                       # noise-free PNG is small, so pad the file
        response = run(client, "blur", data=big + b"\0" * (1024 * 1024 + 1))
        assert response.status_code == 413


def test_pixel_limit_is_413(tmp_path):
    with TestClient(create_app(settings(tmp_path, max_pixels=1000))) as client:
        response = run(client, "blur", data=make_png((100, 100)))
        assert response.status_code == 413 and "megapixels" in response.json()["detail"]


def test_missing_model_is_503_not_a_crash(tmp_path, monkeypatch):
    from engine.models.adapters import mediapipe_selfie

    def offline(url, dest):
        raise OSError("offline")

    monkeypatch.setattr(mediapipe_selfie, "_download", offline)
    with TestClient(create_app(settings(tmp_path))) as client:
        response = run(client, "blur", {"mode": "background"})
        assert response.status_code == 503


def test_unexpected_crash_is_500_without_internals(tmp_path):
    app = create_app(settings(tmp_path))
    with TestClient(app, raise_server_exceptions=False) as client:
        def boom(*a, **k):
            raise RuntimeError("secret internal detail")
        app.state.engine.run = boom
        response = run(client, "blur")
        assert response.status_code == 500 and "secret" not in response.text


# ---- optional token ----------------------------------------------------------
def test_token_protects_tools_but_not_health(tmp_path):
    with TestClient(create_app(settings(tmp_path, token="s3cret"))) as client:
        assert client.get("/api/health").json()["auth_required"] is True
        assert client.get("/api/tools").status_code == 401
        assert run(client, "blur").status_code == 401
        assert client.get("/api/tools", headers={"Authorization": "Bearer wrong"}).status_code == 401
        ok = {"Authorization": "Bearer s3cret"}
        assert client.get("/api/tools", headers=ok).status_code == 200
        assert run(client, "blur", headers=ok).status_code == 200


def test_cors_allows_the_dev_frontend(client):
    response = client.options("/api/tools", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_busy_server_returns_503(tmp_path):
    cfg = settings(tmp_path, queue_timeout_s=0.2)
    with TestClient(create_app(cfg)) as client:
        client.app.state.service._slots.acquire()          # occupy the only slot
        assert run(client, "blur").status_code == 503


# ---- the desktop app talks to this API --------------------------------------
@pytest.fixture(scope="module")
def live_url(tmp_path_factory):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    cfg = Settings(weights_dir=tmp_path_factory.mktemp("w"), device="cpu")
    server = uvicorn.Server(uvicorn.Config(create_app(cfg), host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True


def test_desktop_remote_runner_works_against_this_api(live_url):
    """DesktopApp/runners/remote_runner.py is the other client of this API."""
    from runners.base_runner import RunnerError
    from runners.remote_runner import RemoteRunner

    runner = RemoteRunner(live_url)
    tools = runner.describe_tools()
    assert {"blur", "auto_enhance"} <= {t.name for t in tools}
    assert all(isinstance(p.kind, str) for t in tools for p in t.params)

    source = Image.new("RGB", (50, 40), (10, 200, 10))
    result = runner.run("blur", source, {"strength": 3})
    assert result.size == (50, 40)

    with pytest.raises(RunnerError, match="(?i)mode"):
        runner.run("blur", source, {"mode": "sideways"})
    with pytest.raises(RunnerError, match="teleport"):
        runner.run("teleport", source, {})
