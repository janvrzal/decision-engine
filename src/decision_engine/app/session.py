"""Smyčka událostí a efektů (ADR-0006): reduce → vykonat efekty → nové události → …

Imperativní obal kolem čistého reduceru. Zpracování jedné zprávy uživatele je jeden
trace (Langfuse best practices: trace = jedno kolo dialogu, session = relace).
"""

from collections import deque
from collections.abc import Callable
from dataclasses import asdict

from decision_engine.app.extractor import ExtractionTrace, run_extraction
from decision_engine.app.ports import Ports, RoutingRequest, Turn
from decision_engine.core.effects import CallExtractor, CallRouter, Effect, RunSolver
from decision_engine.core.events import (
    AiFailed,
    Event,
    MessageSent,
    ProposalReceived,
    RouteDecided,
    SolveFinished,
)
from decision_engine.core.reducer import reduce
from decision_engine.core.result import Err, Ok
from decision_engine.core.routing import RouteOutcome, RoutingDecision
from decision_engine.core.state import AppState, current_step

type Publish = Callable[[AppState], None]
"""Zveřejní mezistav (např. s běžící operací), než se vykoná dlouhý efekt."""


def _ignore(_: AppState) -> None:
    return None


def handle(state: AppState, event: Event, ports: Ports, publish: Publish = _ignore) -> AppState:
    """Zpracuje událost včetně všech efektů, které z ní vyplynou, a vrátí nový stav.

    Před každým efektem (volání AI, výpočet) zveřejní mezistav přes `publish`, aby
    obnovená stránka viděla, že operace běží (R5).
    """
    if isinstance(event, MessageSent) and event.text.strip():
        with ports.tracer.turn(
            name="process-message", session_id=state.session_id, input=event.text
        ) as turn:
            new_state = _run(state, event, ports, turn, publish)
            _describe_turn(turn, state, new_state)
            return new_state
    return _run(state, event, ports, None, publish)


def _run(
    state: AppState, event: Event, ports: Ports, turn: Turn | None, publish: Publish
) -> AppState:
    state, effects = reduce(state, event)
    queue: deque[Effect] = deque(effects)
    while queue:
        publish(state)
        result = _execute(queue.popleft(), ports, turn)
        state, more = reduce(state, result)
        queue.extend(more)
    return state


def _execute(effect: Effect, ports: Ports, turn: Turn | None) -> Event:
    match effect:
        case CallRouter():
            decision = _route(effect, ports)
            if turn is not None:
                turn.set_metadata({"routing": decision.model_dump(mode="json")})
            return RouteDecided(decision=decision)
        case CallExtractor():
            event, trace = run_extraction(effect, ports)
            if turn is not None:
                _record_extraction(turn, event, trace)
            return event
        case RunSolver(project=project):
            return SolveFinished(result=ports.solver.solve(project))


def _route(effect: CallRouter, ports: Ports) -> RoutingDecision:
    request = RoutingRequest(message=effect.text, order=effect.order)
    match ports.router.route(request):
        case Ok(decision):
            return decision
        case Err(error):
            # Záložní cesta, kdyby router v portech nebyl řetěz se zálohou: rovnou extrakce.
            return RoutingDecision(
                outcome=RouteOutcome.SUPPORTED,
                capability="cutting_1d",
                router="manual",
                fallback_reason=f"{error.router}: {error.detail}",
            )


def _record_extraction(turn: Turn, event: Event, trace: ExtractionTrace) -> None:
    turn.set_metadata({"extraction": asdict(trace)})
    if isinstance(event, AiFailed):
        turn.fail(f"Extrakce selhala: {event.kind}")
    elif isinstance(event, ProposalReceived):
        turn.set_metadata({"proposal": event.proposal.model_dump(mode="json")})


def _describe_turn(turn: Turn, before: AppState, after: AppState) -> None:
    """Výstup kola = odpověď asistenta; stav zakázky do metadat."""
    new_messages = after.messages[len(before.messages) :]
    replies = [m for m in new_messages if m.role == "assistant"]
    if replies:
        last = replies[-1]
        turn.set_output(last.text if last.kind == "text" else f"chyba: {last.error_kind}")
    turn.set_metadata(
        {
            "base_revision": before.project.revision if before.project else None,
            "step": current_step(after).value,
            "proposal_errors": len(after.proposal_errors),
        }
    )
