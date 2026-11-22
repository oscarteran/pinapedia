"""Servidor HTTP de PiñaPedia: agentes ADK + chat web + protección de la demo.

Local (chat propio):  uv run --env-file app/.env uvicorn main:app --reload
Local (UI de ADK):    uv run adk web
Cloud Run:            el Dockerfile lo arranca en el puerto $PORT.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app

from server.guard import GuardMiddleware

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"

# La UI de desarrollo de ADK queda apagada en producción (ADK_WEB_UI=false).
app = get_fast_api_app(
    agents_dir=str(ROOT),
    web=os.getenv("ADK_WEB_UI", "false").lower() == "true",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# Va al final: envuelve toda la app, incluidas las rutas de ADK.
app.add_middleware(GuardMiddleware)