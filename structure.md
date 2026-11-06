# Image AI Studio: project structure

Every file in the planned tree, with its function. The tree is the one you sent. Each file carries a status tag so you can tell what exists from what is still a plan.

| Tag | Meaning |
|---|---|
| **built** | exists and is tested (or written and waiting for a real-display check, noted where relevant) |
| **added** | exists, but was not in your tree; I added it while building |
| **changed** | exists under a different name or location than in your tree |
| **planned** | in your tree, not created yet |

**Dependency rule:** `engine/` never imports interface, controllers, runners, backend or HTTP code. Everything else depends on the engine, never the reverse.

---

## Overview

```
IMAGE_AI_STUDIO/
├── DesktopApp/     engine + CustomTkinter interface + runners   (built)
├── backend/        FastAPI server that calls the same engine    (planned)
├── frontend/       React + TypeScript PWA                       (planned)
├── .gitignore                                                    (planned)
└── README.md                                                     (planned)
```

---

## Root files

| File | Status | Function |
|---|---|---|
| `.gitignore` | planned | Keeps generated and heavy files out of git: `.venv/`, `__pycache__/`, `DesktopApp/data/`, `DesktopApp/engine/models/weights/*` (except `.gitkeep`), `backend/storage/`, `frontend/node_modules/`, `frontend/dist/`. |
| `README.md` | planned | Repository front page: what the project is, the three folders, how to run each, and links to `DesktopApp/README.md`. |

---

## DesktopApp/

### Top-level files

| File | Status | Function |
|---|---|---|
| `run_desktop.py` | built | The launcher. Loads settings, chooses `LocalRunner` or `RemoteRunner`, builds `MainWindow`, creates `EditorController`, links them, calls `mainloop()`, then closes the runner. Contains no logic. |
| `pyproject.toml` | built | Makes `engine` installable as a package (`pip install -e DesktopApp`) so the backend can `from engine.engine import run`. Includes `manifest.json` as package data and sets the pytest test path. |
| `requirements.txt` | built | Desktop dependencies: customtkinter, pillow, numpy, requests (remote mode only), mediapipe (Blur background mode only), pytest. |
| `README.md` | added | Documentation for this folder: diagrams, setup, configuration, how to add a tool. |
| `ARCHITECTURE.md` | added | Extended architecture notes: request flow, folder responsibilities, the `ToolInfo` contract, backend endpoints. |
| `structure.md` | added | This file. |

### config/

| File | Status | Function |
|---|---|---|
| `__init__.py` | added | Marks the folder as a Python package. |
| `settings.py` | built | `Settings` dataclass (`mode`, `server_url`, `token`, `appearance`). `load_settings()` reads `data/settings.json`, falls back to defaults if the file is missing or broken, then applies environment overrides (`IMAGE_STUDIO_MODE`, `IMAGE_STUDIO_SERVER`, `IMAGE_STUDIO_TOKEN`). `save_settings()` writes it back. |
| `paths.py` | built | Single source of truth for locations: `ROOT`, `DATA_DIR`, `OUTPUT_DIR`, `CACHE_DIR`, `SETTINGS_FILE`. |
| `model_config.py` | planned | Per-model tuning once heavy models arrive (precision, tile size, memory limits). Today `engine/models/manifest.json` covers what is needed, so this file is not created yet. |

### engine/: the shared core

| File | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker. |
| `engine.py` | built | The single entry point for desktop and backend. `Engine` builds the tool registry, `DeviceManager` and `ModelManager`. `run(tool, image, params)` looks up the tool, validates and clamps the params, builds a `ToolContext`, runs the tool, and checks that a PIL image came back. Also provides `list_tools()`, `describe_tools()`, `pipeline()`, and the module-level `get_engine()` and `run()` shortcuts. |
| `tool_registry.py` | built | `ToolRegistry` scans `engine/tools/*/tool.py`, imports each, and stores one instance of every `BaseTool` subclass under its `name`. A tool that fails to import goes into `registry.failed` instead of stopping the app. Provides `get(name)` (raises `ToolNotFound`), `names()`, `infos()`. |
| `base_tool.py` | built | `BaseTool`, the contract every tool follows: class attributes `name`, `label`, `description`, `params`, and the abstract `run(image, params, ctx)`. Also `ToolContext` (gives a tool access to the model manager and device). |
| `pipeline.py` | built | `Pipeline` chains tools: `engine.pipeline().add("auto_enhance").add("blur", {...}).run(image)`. Each step's output is the next step's input. |
| `image_loader.py` | built | `load_image(path)` and `image_from_bytes(data)`. Respects EXIF rotation, normalizes to RGB or RGBA, and detaches from the file handle. |
| `image_exporter.py` | built | `save_image(image, path)` (creates folders, drops alpha for JPEG) and `image_to_bytes(image, fmt)` for sending over HTTP. |
| `device_manager.py` | built | `DeviceManager.device` returns `cuda`, `mps` or `cpu`. Detection is lazy, so the app starts fast even when torch is installed. |
| `model_manager.py` | built | `ModelManager.get(name)` loads an AI model on first use through its adapter, caches it, and is thread-safe. `unload()` frees memory. Models are described in `models/manifest.json`. |
| `errors.py` | added | `EngineError` (base), `ToolNotFound`, `ParamError`, `ModelUnavailable`. Runners and the backend catch `EngineError` to show clean messages. |

#### engine/schemas/: data contracts shared with the backend

| File | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker. |
| `requests.py` | built | `ParamSpec` describes one option of a tool (`name`, `label`, `kind`, `default`, `min`, `max`, `step`, `choices`, `help`). Kinds: `slider`, `int`, `choice`, `bool`, `text`, `color`. `RunRequest` is the tool name plus params. |
| `responses.py` | built | `ToolInfo` is the public description of a tool (what `GET /api/tools` returns), with `to_dict()` and `from_dict()` so it survives JSON. |
| `validation.py` | built | `validate_params(specs, params)` fills defaults, converts types, clamps numbers to min/max, trims text, checks `#rrggbb` colors, and rejects unknown names or invalid choices with `ParamError`. |

#### engine/tools/: one folder per tool

Each tool folder holds a `tool.py` with one `BaseTool` subclass. A tool must return a **new** image and never modify its input. `__init__.py` in each folder is empty.

| Folder | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker the registry scans. |
| `blur/tool.py` | built | `BlurTool`. `mode` = `whole` (Gaussian blur of the full image) or `background` (keeps the person sharp using the segmentation mask). `strength` 1 to 50. |
| `blur/config.py` | planned | Not needed yet; the option list lives in `tool.py`. |
| `auto_enhance/tool.py` | added | `AutoEnhanceTool`: automatic contrast (`contrast_cutoff`), then `color` and `sharpness`. Preserves the alpha channel. |
| `crop/tool.py` | added | `CropTool`: crops to an aspect ratio (`aspect`), with `zoom` and `offset_x` / `offset_y` to move the crop window without leaving the image. |
| `rotate_flip/tool.py` | added | `RotateFlipTool`: 90-degree turns, `straighten` (-45 to 45, canvas grows to fit), mirror left/right, flip upside down. |
| `adjust/tool.py` | added | `AdjustTool`: manual `brightness`, `contrast`, `saturation`, `warmth`. Preserves alpha. |
| `watermark/tool.py` | added | `WatermarkTool`: draws `text` in a chosen `color`, `size` (% of image width), `opacity` and `position`. |
| `background_removal/` | planned | Removes the background to a transparent PNG using the segmentation model (can reuse `selfie_segmenter`). |
| `object_removal/` | planned | Removes a selected object and fills the gap. Needs a mask input and an inpainting model. |
| `inpainting/` | planned | Fills a masked region with generated content. |
| `outpainting/` | planned | Extends the image beyond its borders. |
| `upscaling/` | planned | Enlarges the image 2x or 4x with a super-resolution model. |
| `colorization/` | planned | Adds color to black-and-white photos. |
| `relighting/` | planned | Changes the lighting direction or mood. |
| `style_transfer/` | planned | Applies the look of another image or an art style. |
| `restoration/` | planned | Repairs old or damaged photos (scratches, noise, blur). |

Also on your sketch but not yet in any tree: face blur, image to PDF, image to text.

#### engine/models/: model management

| File | Status | Function |
|---|---|---|
| `manifest.json` | built | The registry of models: each entry names its `adapter`, weights `file`, download `url`, and options such as `invert_mask`. Currently one entry, `selfie_segmenter`. |
| `adapters/__init__.py` | built | Package marker. |
| `adapters/base_adapter.py` | built | `BaseAdapter`: the shape every model wrapper follows (`load()`, `unload()`, plus `name`, `entry`, `device`, `weights_dir`). |
| `adapters/mediapipe_selfie.py` | built (not run end-to-end) | Downloads the `.tflite` model on first use, runs MediaPipe's image segmenter, and exposes `mask(image)` returning a soft person mask. The only place that imports mediapipe. |
| `weights/` | built | Downloaded model files. Git-ignored; only `.gitkeep` is tracked. |

### interface/: CustomTkinter UI

The interface draws widgets and reports clicks. It never calls the engine directly.

| File | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker. |
| `main_window.py` | built (not run on a real display) | `MainWindow`, the root window. Lays out sidebar, workspace and status bar with `grid`. Handles Open/Save dialogs and shortcuts (Ctrl+O, Ctrl+S, Ctrl+Z). Keeps `current_tool`. Provides the view methods the controller calls: `show_image`, `set_busy`, `set_can_undo`, `set_status`, `show_error`. |
| `app.py` | changed | Replaced by `main_window.py`; the root window class lives there, so this file is not created. |
| `workspace.py` | built (not run on a real display) | The right-hand area: toolbar (Open, Save, Undo, Original), tool title, image canvas, and a bottom panel with the tool description, the options panel, and the **Run** and **Reset options** buttons. Reports clicks through callbacks. |
| `sidebar.py` | built (not run on a real display) | Scrollable list with one button per tool, built from the tool list. Highlights the selected tool and reports its `name`. |
| `canvas.py` | built (not run on a real display) | Shows the current image scaled to fit, and re-fits after the window is resized (debounced 80 ms). Display copy only; the full-resolution image stays in memory. |
| `components/__init__.py` | built | Package marker. |
| `components/params_panel.py` | built (not run on a real display) | Builds the bottom controls from a tool's `ParamSpec` list: slider, dropdown, switch, text box, color button. Two columns when a tool has more than three options. `values()` reads the controls; `reset()` restores the defaults. |

### controllers/

| File | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker. |
| `editor_controller.py` | built | `EditorController`: the bridge between window and runner. Holds the current image, the original, and up to 20 undo steps. `open_image`, `save_image`, `run_tool`, `undo`, `reset`. Runs tools on a worker thread and passes the result back through a queue that the UI thread polls every 50 ms, so widgets are only touched from the UI thread. |

### runners/: how the desktop reaches the engine

| File | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker. |
| `base_runner.py` | built | `BaseRunner` interface (`describe_tools`, `run`, `list_tools`, `close`) and `RunnerError`. The only processing API the UI knows. |
| `local_runner.py` | built | Calls `Engine.run()` in the same process and converts `EngineError` to `RunnerError`. Works offline. |
| `remote_runner.py` | built (waiting for the backend) | Sends the image to the FastAPI server: `GET /api/tools`, `POST /api/tools/{name}` (multipart `file` plus JSON `params`), with a Bearer token. Same interface as `LocalRunner`. |

### data/ (git-ignored)

| Path | Status | Function |
|---|---|---|
| `settings.json` | created at runtime | The user's saved settings. |
| `outputs/` | built | Default place for exported images. |
| `cache/` | built | Temporary files. |

### tests/

| File | Status | Function |
|---|---|---|
| `__init__.py` | built | Package marker. |
| `test_engine.py` | built | Tests the registry, validation, every tool, pipelines, model-unavailable handling, `ToolInfo` round-trip and `LocalRunner`. Input images are checked to stay unmodified. |
| `test_controller.py` | added | Tests the controller with a fake view (no display needed): run, undo, reset, errors reaching the UI, saving. |
| `test_tools.py` | planned | Per-tool tests will move here as the tool count grows; they currently live in `test_engine.py`. |

---

## backend/: FastAPI (planned, not started)

The backend contains no image-processing code. Its job is to accept requests, queue work, and call `engine.run()`.

| File | Status | Function |
|---|---|---|
| `main.py` | planned | Creates the FastAPI app, includes the routers, adds CORS for the PWA, and starts the background worker. |
| `requirements.txt` | planned | fastapi, uvicorn, python-multipart, plus an editable install of `DesktopApp` for the engine. |
| `api/routes/auth.py` | planned | Login and token issue. Both clients send `Authorization: Bearer <token>`. |
| `api/routes/images.py` | planned | Upload an image, fetch an uploaded or result image, list the user's images. |
| `api/routes/tools.py` | planned | `GET /api/tools` returns `ToolInfo` for every tool. `POST /api/tools/{name}` takes `file` and `params`, validates, creates a job, and returns the result (or a job id for slow tools). |
| `api/routes/jobs.py` | planned | `GET /api/jobs` and `GET /api/jobs/{id}`: status and result of each job, so the PWA and the desktop app can see the same history. |
| `api/routes/models.py` | planned | Lists available models and whether their weights are downloaded. |
| `api/dependencies.py` | planned | Shared FastAPI dependencies: the current user from the token, the engine instance, the job service. |
| `services/image_service.py` | planned | The only backend code that calls `engine.run()`. Reads the upload, runs the tool, saves the output. |
| `services/job_service.py` | planned | A queue and worker so model inference never blocks a request handler. One heavy job at a time on the GPU; statuses: queued, running, done, failed. |
| `middleware/` | planned | Request logging, error handling that turns `EngineError` into `{"detail": "..."}` with a 4xx status, upload size limits. |
| `storage/uploads/`, `outputs/`, `temporary/` | planned | Where the server keeps uploaded images, finished results, and scratch files. Git-ignored. |
| `tests/test_api.py` | planned | Tests the endpoints with FastAPI's test client, including the contract `RemoteRunner` depends on. |

---

## frontend/: React + TypeScript PWA (planned, not started)

| File | Status | Function |
|---|---|---|
| `package.json` | planned | Dependencies and scripts (React, TypeScript, Vite, PWA plugin, `openapi-typescript`). |
| `vite.config.ts` | planned | Vite build configuration and the dev-server proxy to the backend. |
| `public/manifest.json` | planned | Makes the web app installable: name, icons, theme color, display mode. |
| `public/icons/` | planned | App icons in the sizes the install prompt needs. |
| `src/components/` | planned | Reusable UI pieces: tool sidebar, image viewer, buttons. |
| `src/components/` (option controls) | planned | One control per option kind (`slider`, `int`, `choice`, `bool`, `text`, `color`), mirroring the desktop options panel and built from the same `ToolInfo`. |
| `src/pages/` | planned | Screens: login, editor, job history. |
| `src/editor/` | planned | The editing workspace: loads an image, shows the tool options, sends the request, shows the result, keeps undo history. |
| `src/services/` | planned | API client: `getTools()`, `runTool()`, `getJobs()`, token handling. |
| `src/hooks/` | planned | React hooks such as `useTools`, `useJob` (polls a job until it finishes). |
| `src/types/` | planned | TypeScript types generated from the FastAPI OpenAPI schema, so the frontend and backend cannot drift apart. |

---

## How the pieces connect

```
DesktopApp (local mode):
  interface -> controllers -> LocalRunner -> engine -> tools -> models

DesktopApp (remote mode):
  interface -> controllers -> RemoteRunner --HTTP--> backend -> image_service -> engine

PWA:
  frontend --HTTP--> backend -> image_service -> engine
```

All three paths end in the same `engine.run(tool, image, params)`, so a tool is written once and works everywhere.
