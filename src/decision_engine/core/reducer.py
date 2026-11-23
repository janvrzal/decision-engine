"""Reducer: jediné místo, které mění stav relace (ADR-0006, service design F0).

`reduce(state, event)` je čistá funkce: vrátí nový stav a efekty, nic nevykonává
a nikdy nevyhodí výjimku. Událost, která v daném stavu nedává smysl, stav nezmění.
"""

from decision_engine.core.effects import CallExtractor, Effect, RunSolver
from decision_engine.core.events import (
    AiFailed,
    Event,
    MessageSent,
    ProposalConfirmed,
    ProposalReceived,
    ProposalRejected,
    SolveFinished,
    SolveRequested,
)
from decision_engine.core.model.proposal import confirm_proposal
from decision_engine.core.result import Err, Ok
from decision_engine.core.state import AppState, Message, PendingOperation

type Transition = tuple[AppState, tuple[Effect, ...]]


def reduce(state: AppState, event: Event) -> Transition:
    """Vrátí nový stav a efekty po události."""
    match event:
        case MessageSent(text=text):
            return _message_sent(state, text)
        case ProposalReceived():
            return _proposal_received(state, event)
        case ProposalConfirmed():
            return _proposal_confirmed(state)
        case ProposalRejected():
            return _proposal_rejected(state)
        case SolveRequested():
            return _solve_requested(state)
        case SolveFinished():
            return _solve_finished(state, event)
        case AiFailed():
            return _ai_failed(state, event)


def _unchanged(state: AppState) -> Transition:
    return state, ()


def _with_message(state: AppState, message: Message) -> AppState:
    return state.model_copy(
        update={
            "messages": (*state.messages, message),
            "next_message_id": state.next_message_id + 1,
        }
    )


def _message_sent(state: AppState, text: str) -> Transition:
    text = text.strip()
    if state.pending is not None or not text:
        return _unchanged(state)
    message = Message(id=state.next_message_id, role="user", kind="text", text=text)
    new_state = _with_message(state, message).model_copy(
        update={"pending": PendingOperation(kind="extraction")}
    )
    return new_state, (CallExtractor(text=text, base=state.project),)


def _proposal_received(state: AppState, event: ProposalReceived) -> Transition:
    if state.pending is None or state.pending.kind != "extraction":
        return _unchanged(state)
    new_state = state.model_copy(
        update={"proposal": event.proposal, "proposal_errors": (), "pending": None}
    )
    if event.reply:
        reply = Message(id=state.next_message_id, role="assistant", kind="text", text=event.reply)
        new_state = _with_message(new_state, reply)
    return new_state, ()


def _proposal_confirmed(state: AppState) -> Transition:
    if state.proposal is None or state.pending is not None:
        return _unchanged(state)
    revision = 0 if state.project is None else state.project.revision + 1
    match confirm_proposal(state.proposal, state.session_id, revision):
        case Err(errors):
            return state.model_copy(update={"proposal_errors": errors}), ()
        case Ok(project):
            new_state = state.model_copy(
                update={
                    "project": project,
                    "proposal": None,
                    "proposal_errors": (),
                    "pending": PendingOperation(kind="solving", revision=project.revision),
                }
            )
            return new_state, (RunSolver(project=project),)


def _proposal_rejected(state: AppState) -> Transition:
    if state.proposal is None:
        return _unchanged(state)
    return state.model_copy(update={"proposal": None, "proposal_errors": ()}), ()


def _solve_requested(state: AppState) -> Transition:
    if state.project is None or state.pending is not None:
        return _unchanged(state)
    pending = PendingOperation(kind="solving", revision=state.project.revision)
    return state.model_copy(update={"pending": pending}), (RunSolver(project=state.project),)


def _solve_finished(state: AppState, event: SolveFinished) -> Transition:
    pending = state.pending
    is_awaited = (
        pending is not None
        and pending.kind == "solving"
        and pending.revision == event.result.source.revision
    )
    if not is_awaited:
        # Zastaralý výsledek nesmí přepsat novější stav.
        return _unchanged(state)
    return state.model_copy(update={"result": event.result, "pending": None}), ()


def _ai_failed(state: AppState, event: AiFailed) -> Transition:
    if state.pending is None or state.pending.kind != "extraction":
        return _unchanged(state)
    error = Message(id=state.next_message_id, role="assistant", kind="error", error_kind=event.kind)
    return _with_message(state, error).model_copy(update={"pending": None}), ()
