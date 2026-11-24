"""Ověření souboru zakázky bez relace (UC-06, F4): nejdřív platnost, potom dotaz na zahození."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from decision_engine.core.project_file import read_project_file
from decision_engine.core.result import Err, Ok


class FileCheckRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    content: str = Field(max_length=1_000_000)


class FileCheckResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool
    message: str | None = None
    """Proč soubor nejde načíst; česky pro uživatele."""


def project_files_router() -> APIRouter:
    router = APIRouter(prefix="/api/project-files", tags=["project-files"])

    @router.post("/check", summary="Ověřit soubor zakázky")
    def check_file(request: FileCheckRequest) -> FileCheckResponse:  # pyright: ignore[reportUnusedFunction]
        match read_project_file(request.content):
            case Err(message):
                return FileCheckResponse(ok=False, message=message)
            case Ok():
                return FileCheckResponse(ok=True)

    return router
