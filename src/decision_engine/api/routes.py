"""Endpointy relací (ADR-0006): frontend posílá události a dostává view model."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException
from pydantic import Field

from decision_engine.api.sessions import SessionNotFoundError, SessionStore
from decision_engine.api.view_builder import build_view_model
from decision_engine.api.view_model import ViewModel
from decision_engine.app.ports import Ports
from decision_engine.app.session import handle
from decision_engine.core.events import (
    MessageSent,
    ProposalConfirmed,
    ProposalEdited,
    ProposalRejected,
    SolveRequested,
)
from decision_engine.core.state import AppState

type UserEvent = Annotated[
    MessageSent | ProposalEdited | ProposalConfirmed | ProposalRejected | SolveRequested,
    Field(discriminator="type"),
]
"""Jen události, které smí poslat uživatel; výsledky efektů (návrh od AI, výsledek
solveru, chyba AI) zvenku poslat nejde."""


@dataclass(frozen=True, slots=True)
class Services:
    """Závislosti endpointů sestavené v `create_app`."""

    store: SessionStore
    ports: Ports
    extraction_available: bool
    on_shutdown: Callable[[], None]
    """Úklid při ukončení aplikace (odeslání trasování do Langfuse)."""


def session_router(services: Services) -> APIRouter:
    router = APIRouter(prefix="/api/sessions", tags=["sessions"])

    def view(state: AppState) -> ViewModel:
        return build_view_model(state, extraction_available=services.extraction_available)

    @router.post("", summary="Založit relaci")
    def create_session() -> ViewModel:  # pyright: ignore[reportUnusedFunction]
        return view(services.store.create())

    @router.get(
        "/{session_id}",
        summary="Stav relace",
        responses={404: {"description": "Relace neexistuje (např. po restartu serveru)."}},
    )
    def get_session(session_id: str) -> ViewModel:  # pyright: ignore[reportUnusedFunction]
        try:
            return view(services.store.get(session_id))
        except SessionNotFoundError as error:
            raise _not_found() from error

    @router.post(
        "/{session_id}/events",
        summary="Poslat událost",
        responses={404: {"description": "Relace neexistuje (např. po restartu serveru)."}},
    )
    def post_event(  # pyright: ignore[reportUnusedFunction]
        session_id: str, event: Annotated[UserEvent, Body()]
    ) -> ViewModel:
        try:
            state = services.store.update(
                session_id, lambda current: handle(current, event, services.ports)
            )
        except SessionNotFoundError as error:
            raise _not_found() from error
        return view(state)

    return router


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "session_not_found", "message": "Relace neexistuje."},
    )
