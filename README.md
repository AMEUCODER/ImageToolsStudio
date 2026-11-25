# Image Tools Studio

One Python image engine, three front doors.

| Folder | What it is |
|---|---|
| `DesktopApp/` | The engine (`engine/`) and the CustomTkinter desktop app |
| `backend/` | FastAPI service exposing the same engine at `/api` |
| `frontend/` | React + TypeScript PWA (installable, light/dark) |

## Run locally

```bash
# backend  (http://127.0.0.1:8000)
cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000

# frontend (http://localhost:5173, proxies /api to the backend)
cd frontend && npm install && npm run dev
```

## Run with Docker

```bash
docker compose up --build        # open http://localhost:8080
```

Set `IMAGE_STUDIO_TOKEN` to require a Bearer token. Model weights are kept in the `weights` volume.

## Tests

```bash
cd backend && pip install -r requirements-dev.txt && pytest
cd frontend && npm run typecheck
```

## Status

In development. The desktop app, the FastAPI backend and the React PWA all exist and share one engine with 7 tools: Blur, Auto Enhance, Crop, Rotate / Flip, Adjust, Text Watermark and Face Blur. See [`DesktopApp/README.md`](DesktopApp/README.md) for the engine design.

## To do

- [ ] Run the desktop app on a real display and fix visual issues
- [ ] Add frontend tests (only `npm run typecheck` runs today)
- [ ] Add a GitHub Actions workflow for the backend tests, the desktop tests and the frontend typecheck
- [ ] Add screenshots of the desktop app and the PWA to this README
- [ ] Add the planned tools: background removal, object removal, inpainting, outpainting, upscaling, colorization, relighting, style transfer, image to PDF, image to text
- [ ] Update `DesktopApp/README.md`, where the status section is out of date
