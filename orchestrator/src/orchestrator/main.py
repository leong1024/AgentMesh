"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from shared.env_load import load_local_env

from orchestrator.dependencies import get_settings
from orchestrator.routes_analyze import router as analyze_router


def create_app() -> FastAPI:
    load_local_env()
    settings = get_settings()
    app = FastAPI(title="AgentMesh Orchestrator", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(analyze_router)

    if settings.static_dir:
        static_path = Path(settings.static_dir)
        if static_path.is_dir():
            assets = static_path / "assets"
            if assets.is_dir():
                app.mount("/assets", StaticFiles(directory=assets), name="assets")

            @app.get("/")
            async def spa_index():
                from fastapi.responses import FileResponse

                index = static_path / "index.html"
                if index.is_file():
                    return FileResponse(index)
                return {"detail": "Run frontend build first"}

    return app
