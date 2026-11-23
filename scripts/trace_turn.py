"""Jedno kolo UC-01 se skutečnými adaptéry: zpráva → extrakce přes model → návrh změny.

    uv run --env-file .env python scripts/trace_turn.py ["vlastní zadání"]

Slouží k ověření extrakce a trasování v Langfuse. Vypíše návrh a id session; trace
najdete v Langfuse pod touto session.
"""

import sys
import uuid

from decision_engine.adapters.config import build_ai_adapters
from decision_engine.app.ports import Ports
from decision_engine.app.session import handle
from decision_engine.core.events import MessageSent
from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.state import initial_state

DEFAULT_MESSAGE = (
    "Potřebuju deset jeklů 40×40 po 2 m a pět příček po 1,5 m, "
    "kupuju šestimetrové tyče po 420 Kč, prořez 3 mm."
)


class NoSolver:
    """Skript končí návrhem změny; solver (#12) se nevolá."""

    def solve(self, project: Project) -> CalculationResult:
        raise NotImplementedError("Solver přijde v #12.")


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MESSAGE
    ai = build_ai_adapters()
    ports = Ports(llm=ai.llm, prompts=ai.prompts, tracer=ai.tracer, solver=NoSolver())
    session_id = f"skript-{uuid.uuid4().hex[:8]}"

    state = handle(initial_state(session_id), MessageSent(text=message), ports)
    ai.tracer.flush()

    print(f"Langfuse: {'zapnutý' if ai.langfuse_enabled else 'vypnutý'}, session {session_id}")
    for chat_message in state.messages:
        print(f"[{chat_message.role}] {chat_message.text or chat_message.error_kind}")
    if state.proposal is not None:
        print(state.proposal.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
