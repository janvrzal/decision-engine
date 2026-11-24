"""Úložiště relací: mezistav během dlouhé operace a návrat při chybě."""

from collections.abc import Callable

import pytest

from decision_engine.api.sessions import SessionStore
from decision_engine.core.state import AppState, PendingOperation


def test_mezistav_je_videt_uz_behem_zmeny() -> None:
    store = SessionStore()
    session_id = store.create().session_id
    seen: list[PendingOperation | None] = []

    def change(state: AppState, publish: Callable[[AppState], None]) -> AppState:
        publish(state.model_copy(update={"pending": PendingOperation(kind="solving")}))
        seen.append(store.get(session_id).pending)
        return state

    final = store.update(session_id, change)

    assert seen == [PendingOperation(kind="solving")]
    assert final.pending is None
    assert store.get(session_id).pending is None


def test_pri_chybe_se_vrati_puvodni_stav() -> None:
    store = SessionStore()
    before = store.create()

    def change(state: AppState, publish: Callable[[AppState], None]) -> AppState:
        publish(state.model_copy(update={"pending": PendingOperation(kind="extraction")}))
        raise RuntimeError("výpadek")

    with pytest.raises(RuntimeError):
        store.update(before.session_id, change)

    assert store.get(before.session_id) == before
