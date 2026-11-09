# Backend: FastAPI + the shared engine from DesktopApp.
# Build from the repository root so DesktopApp is in the build context:
#   docker build -f backend/Dockerfile -t image-studio-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    IMAGE_STUDIO_WEIGHTS_DIR=/weights

# opencv-python-headless needs no GUI libraries; libgomp1 is for numpy/opencv threading.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# 1) the engine, installed as a package (pyproject packages `engine*`)
COPY DesktopApp /tmp/DesktopApp
RUN pip install /tmp/DesktopApp && rm -rf /tmp/DesktopApp

# 2) the backend's own dependencies, then its code
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .

# run as a non-root user; /weights holds downloaded model files
RUN useradd --create-home app && mkdir -p /weights && chown app /weights
USER app
VOLUME /weights

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
  CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
