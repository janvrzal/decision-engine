"""Relace v paměti (ADR-0006: lokální běh, jeden uživatel; trvalé jsou jen uložené zakázky).

Zpracování události volá AI a solver a trvá sekundy, proto má každá relace zámek:
dvě události téže relace se nezpracují souběžně a stav se nepřepíše.
"""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field

from decision_engine.core.state import AppState, initial_state


class SessionNotFoundError(KeyError):
    """Relace neexistuje (např. po restartu serveru)."""


@dataclass
class _Session:
    state: AppState
    lock: threading.Lock = field(default_factory=threading.Lock)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._guard = threading.Lock()

    def create(self) -> AppState:
        state = initial_state(uuid.uuid4().hex)
        with self._guard:
            self._sessions[state.session_id] = _Session(state)
        return state

    def get(self, session_id: str) -> AppState:
        return self._session(session_id).state

    def update(self, session_id: str, change: Callable[[AppState], AppState]) -> AppState:
        """Provede změnu stavu pod zámkem relace a uloží výsledek."""
        session = self._session(session_id)
        with session.lock:
            session.state = change(session.state)
            return session.state

    def _session(self, session_id: str) -> _Session:
        with self._guard:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session
