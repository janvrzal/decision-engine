"""Jedno kolo UC-01 se skutečnými adaptéry: zpráva → extrakce přes model → návrh změny.

    uv run --env-file .env python scripts/trace_turn.py ["vlastní zadání"]

Slouží k ověření extrakce a trasování v Langfuse. Vypíše návrh, potvrdí ho a vypíše
plán ze solveru; trace najdete v Langfuse pod vypsanou session.
"""

import sys
import uuid

from decision_engine.adapters.config import build_ai_adapters
from decision_engine.app.ports import Ports
from decision_engine.app.session import handle
from decision_engine.app.solving import RegistrySolver
from decision_engine.core.events import MessageSent, ProposalConfirmed
from decision_engine.core.state import initial_state

DEFAULT_MESSAGE = (
    "Potřebuju deset jeklů 40×40 po 2 m a pět příček po 1,5 m, "
    "kupuju šestimetrové tyče po 420 Kč, prořez 3 mm."
)


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MESSAGE
    ai = build_ai_adapters()
    ports = Ports(llm=ai.llm, prompts=ai.prompts, tracer=ai.tracer, solver=RegistrySolver())
    session_id = f"skript-{uuid.uuid4().hex[:8]}"

    state = handle(initial_state(session_id), MessageSent(text=message), ports)
    ai.tracer.flush()

    print(f"Langfuse: {'zapnutý' if ai.langfuse_enabled else 'vypnutý'}, session {session_id}")
    for chat_message in state.messages:
        print(f"[{chat_message.role}] {chat_message.text or chat_message.error_kind}")
    if state.proposal is None:
        return
    print(state.proposal.model_dump_json(indent=2))

    # Potvrzení návrhu jako „Potvrdit a vypočítat“: nová revize a výpočet plánu.
    state = handle(state, ProposalConfirmed(), ports)
    for error in state.proposal_errors:
        print(f"Chyba v návrhu {error.path}: {error.message}")
    if state.result is not None:
        result = state.result
        print(f"Plán ({result.status.value}): {result.metrics.model_dump_json()}")
        for index, bar in enumerate(result.bars, start=1):
            cuts = ", ".join(f"{p.part_id}@{p.start_mm}" for p in bar.pieces)
            print(f"  tyč {index} ({bar.length_mm} mm): {cuts}")


if __name__ == "__main__":
    main()
