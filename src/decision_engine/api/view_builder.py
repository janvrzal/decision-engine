"""Sestavení view modelu ze stavu relace: čisté mapování, odvozené hodnoty z jádra.

Texty jsou podle docs/design-system/obsah.md (krátké, v jazyce dílny, chyba = co se
stalo a co udělat).
"""

from decision_engine.api.view_model import (
    AiView,
    CapabilityView,
    MessageView,
    PendingOperationView,
    ProjectView,
    SessionView,
    StepState,
    StepView,
    ViewModel,
)
from decision_engine.api.view_proposal import build_proposal
from decision_engine.api.view_result import build_result
from decision_engine.capabilities.registry import CAPABILITIES
from decision_engine.core.extraction import DEFAULT_PROJECT_NAME
from decision_engine.core.state import AppState, Message, Step, current_step, is_result_stale

AI_ERROR_TEXT = {
    "connection": "AI teď neodpovídá. Zkuste to znovu za chvíli.",
    "rate_limit": "AI je teď přetížená (vyčerpaný limit). Zkuste to znovu za minutu.",
    "invalid_response": (
        "AI vrátila odpověď, které aplikace nerozumí. Zkuste zadání napsat jinak "
        "nebo to zkuste znovu."
    ),
}
PENDING_LABEL = {
    "extraction": "Připravuji údaje ke kontrole…",
    "solving": "Počítám plán…",
}
STEP_LABEL = {Step.INPUT: "Zadání", Step.REVIEW: "Kontrola údajů", Step.RESULT: "Plán a cena"}


def build_view_model(state: AppState, *, extraction_available: bool) -> ViewModel:
    """View model celé relace."""
    step = current_step(state)
    stale = is_result_stale(state)
    project_name = (
        state.project.name
        if state.project
        else (state.proposal.name if state.proposal and state.proposal.name else None)
    )
    return ViewModel(
        session=SessionView(
            id=state.session_id, ai=AiView(extraction_available=extraction_available)
        ),
        capabilities=tuple(CapabilityView(id=c.id, label=c.label) for c in CAPABILITIES),
        project=ProjectView(
            name=project_name or DEFAULT_PROJECT_NAME,
            revision=state.project.revision if state.project else None,
            step=step.value,
            steps=_steps(state, step, stale),
            has_content=bool(state.project or state.proposal or state.messages),
            can_edit=state.project is not None and state.proposal is None and state.pending is None,
            can_save=state.project is not None,
            save_note=(
                "Rozpracované změny v návrhu nebudou součástí souboru."
                if state.project is not None and state.proposal is not None
                else None
            ),
        ),
        pending_operation=(
            PendingOperationView(kind=state.pending.kind, label=PENDING_LABEL[state.pending.kind])
            if state.pending
            else None
        ),
        messages=tuple(_message(m) for m in state.messages),
        proposal=build_proposal(state.proposal, state.session_id) if state.proposal else None,
        result=build_result(state.result, stale=stale, proposal_pending=state.proposal is not None)
        if state.result
        else None,
        import_error=state.import_error,
    )


def _steps(state: AppState, step: Step, stale: bool) -> tuple[StepView, ...]:
    """Stavy kroků pro StepIndicator (komponenty.md)."""
    review: StepState = (
        "active" if step is Step.REVIEW else "done" if state.project else "unavailable"
    )
    result: StepState
    if state.result is not None:
        result = "stale" if stale else ("active" if step is Step.RESULT else "done")
    elif state.project is not None:
        result = "active" if step is Step.RESULT else "pending"
    else:
        result = "unavailable"
    states: dict[Step, StepState] = {
        Step.INPUT: "active" if step is Step.INPUT else "done",
        Step.REVIEW: review,
        Step.RESULT: result,
    }
    return tuple(StepView(id=s.value, label=STEP_LABEL[s], state=states[s]) for s in Step)


def _message(message: Message) -> MessageView:
    text = message.text
    if message.kind == "error":
        text = AI_ERROR_TEXT.get(message.error_kind or "", AI_ERROR_TEXT["connection"])
    return MessageView(id=message.id, role=message.role, kind=message.kind, text=text)
