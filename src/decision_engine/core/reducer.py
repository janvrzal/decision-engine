"""Reducer: jediné místo, které mění stav relace (ADR-0006, service design F0).

`reduce(state, event)` je čistá funkce: vrátí nový stav a efekty, nic nevykonává
a nikdy nevyhodí výjimku. Událost, která v daném stavu nedává smysl, stav nezmění.
"""

from decision_engine.core.effects import CallExtractor, Effect, RunSolver
from decision_engine.core.events import (
    AiFailed,
    EditRequested,
    Event,
    MessageSent,
    NewProjectRequested,
    ProjectImported,
    ProjectSaved,
    ProposalConfirmed,
    ProposalEdited,
    ProposalReceived,
    ProposalRejected,
    SolveFinished,
    SolveRequested,
    ToolSelected,
)
from decision_engine.core.extraction import empty_proposal
from decision_engine.core.model.proposal import (
    ChangeProposal,
    confirm_proposal,
    inputs_fingerprint,
    proposal_from_project,
)
from decision_engine.core.model.proposal_edit import edit_proposal
from decision_engine.core.project_file import read_project_file
from decision_engine.core.result import Err, Ok
from decision_engine.core.state import AppState, Message, PendingOperation, initial_state

type Transition = tuple[AppState, tuple[Effect, ...]]


def reduce(state: AppState, event: Event) -> Transition:
    """Vrátí nový stav a efekty po události."""
    if state.import_error is not None and not isinstance(event, ProjectImported):
        # Chyba načtení patří jen k poslednímu pokusu; další akce ji schová.
        state = state.model_copy(update={"import_error": None})
    match event:
        case MessageSent(text=text):
            return _message_sent(state, text)
        case ToolSelected():
            return _manual_proposal(state, empty_proposal(), needs_project=False)
        case EditRequested():
            if state.project is None:
                return _unchanged(state)
            return _manual_proposal(state, proposal_from_project(state.project), needs_project=True)
        case ProjectImported(content=content):
            return _project_imported(state, content)
        case ProjectSaved(revision=revision):
            return _project_saved(state, revision)
        case NewProjectRequested():
            if state.pending is not None:
                return _unchanged(state)
            return initial_state(state.session_id), ()
        case ProposalReceived():
            return _proposal_received(state, event)
        case ProposalEdited():
            return _proposal_edited(state, event)
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


def _manual_proposal(
    state: AppState, proposal: ChangeProposal, *, needs_project: bool
) -> Transition:
    """Ruční návrh: nová zakázka bez AI, nebo úprava potvrzené zakázky (UC-13)."""
    has_project = state.project is not None
    if state.pending is not None or state.proposal is not None or has_project != needs_project:
        return _unchanged(state)
    update = {
        "proposal": proposal,
        "proposal_errors": (),
        "proposal_start": inputs_fingerprint(proposal),
    }
    return state.model_copy(update=update), ()


def _project_saved(state: AppState, revision: int) -> Transition:
    """Soubor stažený v aktuální revizi je uložená práce; starší revize ne (UC-06)."""
    if state.project is None or state.project.revision != revision:
        return _unchanged(state)
    saved = inputs_fingerprint(proposal_from_project(state.project))
    return state.model_copy(update={"saved_inputs": saved}), ()


def _imported_text(broken: int) -> str:
    if broken == 0:
        return "Zakázka načtena. Zkontrolujte údaje a spusťte výpočet."
    values = "hodnota měla" if broken == 1 else ("hodnoty měly" if broken <= 4 else "hodnot mělo")
    return (
        f"Zakázka načtena, ale {broken} {values} v souboru nečekaný tvar. "
        "Jsou v tabulce prázdné a označené, doplňte je a spusťte výpočet."
    )


def _project_imported(state: AppState, content: str) -> Transition:
    """Načtený soubor začne novou zakázku jako návrh ke kontrole; plán se nepočítá (UC-06)."""
    if state.pending is not None:
        return _unchanged(state)
    match read_project_file(content):
        case Err(message):
            return state.model_copy(update={"import_error": message}), ()
        case Ok(proposal):
            note = Message(
                id=state.next_message_id,
                role="assistant",
                kind="text",
                text=_imported_text(len(proposal.file_errors)),
            )
            fresh = state.model_copy(
                update={
                    "project": None,
                    "proposal": proposal,
                    "proposal_errors": (),
                    "proposal_start": None,
                    "saved_inputs": inputs_fingerprint(proposal),
                    "result": None,
                    "messages": (note,),
                    "next_message_id": state.next_message_id + 1,
                    "import_error": None,
                }
            )
            return fresh, ()


def _proposal_received(state: AppState, event: ProposalReceived) -> Transition:
    if state.pending is None or state.pending.kind != "extraction":
        return _unchanged(state)
    new_state = state.model_copy(
        update={
            "proposal": event.proposal,
            "proposal_errors": (),
            "proposal_start": None,
            "pending": None,
        }
    )
    if event.reply:
        reply = Message(id=state.next_message_id, role="assistant", kind="text", text=event.reply)
        new_state = _with_message(new_state, reply)
    return new_state, ()


def _proposal_edited(state: AppState, event: ProposalEdited) -> Transition:
    if state.proposal is None or state.pending is not None:
        return _unchanged(state)
    proposal = edit_proposal(
        state.proposal,
        name=event.name,
        material=event.material,
        parts=event.parts,
        stock=event.stock,
        parameters=event.parameters,
    )
    return state.model_copy(update={"proposal": proposal, "proposal_errors": ()}), ()


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
                    "proposal_start": None,
                    "pending": PendingOperation(kind="solving", revision=project.revision),
                }
            )
            return new_state, (RunSolver(project=project),)


def _proposal_rejected(state: AppState) -> Transition:
    if state.proposal is None:
        return _unchanged(state)
    update = {"proposal": None, "proposal_errors": (), "proposal_start": None}
    return state.model_copy(update=update), ()


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
