"""Aplikace FastAPI: endpointy pod `/api` a servírování sestaveného frontendu (ADR-0007)."""

from importlib.metadata import version
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, ConfigDict

_FRONTEND_MISSING_HTML = """<!doctype html>
<html lang="cs">
<head><meta charset="utf-8"><title>DecisionEngine</title></head>
<body>
<h1>Frontend není sestavený</h1>
<p>Ve složce <code>frontend/</code> spusťte <code>pnpm install</code> a <code>pnpm build</code>,
potom aplikaci spusťte znovu. Pro vývoj použijte <code>pnpm dev</code>.</p>
<p>API běží: <a href="/api/health">/api/health</a></p>
</body>
</html>
"""


class HealthResponse(BaseModel):
    """Stav backendu pro kontrolu spojení z frontendu."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    version: str


def create_app(static_dir: Path | None) -> FastAPI:
    """Vytvoří aplikaci; `static_dir` je složka sestaveného frontendu, nebo `None`."""
    app = FastAPI(title="DecisionEngine", version=version("decision-engine"))

    @app.get("/api/health", tags=["system"])
    def health() -> HealthResponse:  # pyright: ignore[reportUnusedFunction]
        return HealthResponse(status="ok", version=app.version)

    index = static_dir / "index.html" if static_dir is not None else None
    has_frontend = index is not None and index.is_file()

    @app.get("/{path:path}", include_in_schema=False, response_model=None)
    def frontend(path: str) -> FileResponse | HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Neznámý endpoint API.")
        if static_dir is None or index is None or not has_frontend:
            return HTMLResponse(_FRONTEND_MISSING_HTML, status_code=503)
        root = static_dir.resolve()
        candidate = (root / path).resolve()
        if path and candidate.is_relative_to(root) and candidate.is_file():
            return FileResponse(candidate)
        # SPA: o všech ostatních cestách rozhoduje router frontendu.
        return FileResponse(index)

    return app
