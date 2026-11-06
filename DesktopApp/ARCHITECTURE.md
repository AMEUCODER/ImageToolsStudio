# Image AI Studio: architecture map

## The one rule

`engine/` knows nothing about windows, HTTP or runners. Everything else depends on it, never the reverse.

```
 CustomTkinter window                     React PWA (frontend/)
 interface/ + controllers/                        |
        |                                         | HTTP
        v                                         v
 runners/  (the only thing the UI calls)    backend/ (FastAPI)
   LocalRunner ------------------+                |
   RemoteRunner --- HTTP ---> backend/ -----------+
                                 |
                                 v
                    engine.run(tool, image, params)
                                 |
        +------------------------+-------------------------+
        v                        v                         v
  tool_registry            schemas/validation        model_manager
  (finds engine/tools/*)   (fills defaults, clamps)  (loads models once)
        |                                                   |
        v                                                   v
  tools/<name>/tool.py  ---- ctx.models.get("x") ---->  models/adapters/<x>.py
```

## Request flow: the user clicks "Run" on Blur

1. `Workspace` collects values from `ParamsPanel` and calls `MainWindow._run(params)`.
2. `EditorController.run_tool("blur", params)` disables Run and starts a worker thread.
3. The worker calls `runner.run("blur", image, params)`.
   - `LocalRunner` calls `Engine.run(...)` in-process.
   - `RemoteRunner` POSTs the image to `/api/tools/blur`; the backend calls the same `Engine.run(...)`.
4. `Engine.run` finds the tool, validates and clamps params, builds a `ToolContext`, and calls `tool.run(image, params, ctx)`.
5. The result goes into a queue. The UI thread polls it every 50 ms, shows the image, and pushes the old image onto the undo stack.

## Folder responsibilities

| Path | Responsibility | Must NOT |
|---|---|---|
| `run_desktop.py` | Pick runner, build window + controller, `mainloop()` | contain logic |
| `config/` | settings.json, paths | import `engine` internals |
| `engine/engine.py` | `Engine.run / list_tools / describe_tools`, module-level `run()` | import UI or HTTP code |
| `engine/base_tool.py` | `BaseTool` contract + `ToolContext` | |
| `engine/tool_registry.py` | Auto-discovers `engine/tools/*/tool.py`; broken tools go to `registry.failed` | |
| `engine/schemas/` | `ParamSpec`, `ToolInfo`, `validate_params`: shared with the backend | |
| `engine/model_manager.py` | Lazy-load + cache models from `models/manifest.json` | |
| `engine/models/adapters/` | One wrapper per model family (the only place that imports model libraries) | |
| `engine/device_manager.py` | cuda / mps / cpu, detected lazily | |
| `engine/image_loader.py`, `image_exporter.py` | Disk/bytes <-> PIL (EXIF rotation, JPEG alpha) | |
| `engine/pipeline.py` | Chain tools: `engine.pipeline().add("a").add("b").run(img)` | |
| `runners/` | `BaseRunner` interface, `LocalRunner`, `RemoteRunner` | |
| `controllers/` | Image + undo history, worker thread, queue polling | touch widgets from a thread |
| `interface/main_window.py` | Root window, shortcuts, file dialogs, the "view" API the controller calls | call the engine |
| `interface/workspace.py` | Toolbar, canvas, options + Run button; reports clicks via callbacks | know about runners |
| `interface/components/params_panel.py` | Builds controls from `ParamSpec` | hardcode tool options |

## How to add a tool (e.g. `face_blur`)

1. Create `engine/tools/face_blur/` with an empty `__init__.py` and a `tool.py`:
   a `BaseTool` subclass with `name`, `label`, `description`, `params = [ParamSpec(...)]`, and `run(image, params, ctx)` that returns a **new** image.
2. If it needs a model: add an entry to `engine/models/manifest.json`, write `engine/models/adapters/<x>.py` (class `Adapter`), and call `ctx.models.get("<name>")` inside `run`.
3. Done. The registry finds it, the sidebar shows it, the options panel builds itself, and the API exposes it. No other file changes.

## Contracts

`ToolInfo` (what `describe_tools()` returns and what `GET /api/tools` must return):

```json
{ "name": "blur", "label": "Blur", "description": "...",
  "params": [ { "name": "strength", "label": "Strength", "kind": "slider",
                "default": 10, "min": 1, "max": 50, "step": 1, "choices": [], "help": "" } ] }
```

`ParamSpec.kind` is one of `slider`, `int`, `choice`, `bool`. The PWA renders the same four controls.

Backend endpoints `RemoteRunner` expects:

- `GET /api/tools` returns a list of `ToolInfo`.
- `POST /api/tools/{name}`: multipart `file` (image) + `params` (JSON string); returns PNG bytes, or `{"detail": "..."}` with a 4xx/5xx status.
- Auth: `Authorization: Bearer <token>`.

## Status

| Piece | State |
|---|---|
| Engine core, registry, validation, pipeline, model manager | working, tested (14 tests) |
| Tools: `blur` (whole), `auto_enhance` | working, tested |
| Tool: `blur` (background mode) | written, **not yet run end-to-end** (needs mediapipe + a model download) |
| Controller (threading, undo, reset, save) | working, tested with a fake view |
| CustomTkinter window | written, **not yet launched** (no display in the build sandbox) |
| `RemoteRunner` | written, waits for the FastAPI backend |
| Other 8+ tools, backend, frontend | not started |
