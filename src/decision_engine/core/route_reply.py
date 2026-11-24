"""Odpověď aplikace na rozhodnutí routeru (UC-05, ADR-0012); část reduceru.

Podporované zadání jde do extrakce. Nejasné a nepodporované dostane odpověď s textem
z `core/routing.py` a nabídkou ručního zadání; dotaz na cenu odpoví spočítaná cena
materiálu, nikdy odhad modelu (pravidlo 8).
"""

from decision_engine.core.costing import material_cost
from decision_engine.core.effects import CallExtractor, Effect
from decision_engine.core.routing import (
    NO_PLAN_COST_TEXT,
    RESULT_QUESTION_TEXT,
    UNCLEAR_TEXT,
    UNSUPPORTED_TEXT,
    RouteOutcome,
    RoutingDecision,
    cost_text,
)
from decision_engine.core.state import AppState, Message, is_result_stale

type Transition = tuple[AppState, tuple[Effect, ...]]


def route_decided(state: AppState, decision: RoutingDecision) -> Transition:
    """Podporované zadání jde do extrakce; jinak aplikace odpoví sama (UC-05)."""
    if state.pending is None or state.pending.kind != "extraction":
        return state, ()
    text = next((m.text for m in reversed(state.messages) if m.role == "user"), "")
    match decision.outcome, decision.capability, decision.intent:
        case RouteOutcome.UNCLEAR, _, _:
            return _reply(state, decision.question or UNCLEAR_TEXT, offer_manual=True)
        case RouteOutcome.UNSUPPORTED, _, _:
            return _reply(state, UNSUPPORTED_TEXT, offer_manual=True)
        case _, "cost_estimate", _ if state.project is not None:
            fresh = state.result is not None and not is_result_stale(state)
            if not fresh or state.result is None:
                return _reply(state, NO_PLAN_COST_TEXT, offer_manual=False)
            return _reply(state, cost_text(material_cost(state.result).total), offer_manual=False)
        case _, "cutting_1d", "result_question" if state.project is not None:
            return _reply(state, RESULT_QUESTION_TEXT, offer_manual=False)
        case _:
            return state, (CallExtractor(text=text, base=state.project),)


def _reply(state: AppState, text: str, *, offer_manual: bool) -> Transition:
    reply = Message(
        id=state.next_message_id,
        role="assistant",
        kind="text",
        text=text,
        offer_manual=offer_manual,
    )
    return (
        state.model_copy(
            update={
                "messages": (*state.messages, reply),
                "next_message_id": state.next_message_id + 1,
                "pending": None,
            }
        ),
        (),
    )
