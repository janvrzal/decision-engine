"""Stav relace `AppState` a jeho odvozené vlastnosti (ADR-0006, spec kap. 7).

Stav mění jen `reduce`. Odvozené vlastnosti (neaktuální plán, krok pracovní plochy)
se počítají z ostatních polí a nikde se neukládají (R3).
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.errors import FieldError
from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import (
    ChangeProposal,
    inputs_fingerprint,
    proposal_from_project,
)


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


type AiErrorKind = Literal["connection", "rate_limit", "invalid_response"]
"""Druh selhání AI; český text pro uživatele skládá view model."""


class Message(_Frozen):
    """Zpráva v Panelu Dialog."""

    id: int
    role: Literal["user", "assistant"]
    kind: Literal["text", "error"]
    text: str = ""
    error_kind: AiErrorKind | None = None
    retry_text: str | None = None
    """U chyby AI text zprávy, kterou jde poslat znovu („Zkusit znovu“ i po obnovení)."""


class PendingOperation(_Frozen):
    """Právě běžící dlouhá operace (R5)."""

    kind: Literal["extraction", "solving"]
    revision: int | None = None
    """U výpočtu revize zakázky, pro kterou běží."""


class AppState(_Frozen):
    """Celý stav jedné relace."""

    session_id: str
    project: Project | None = None
    """Poslední potvrzená revize zakázky."""
    proposal: ChangeProposal | None = None
    proposal_errors: tuple[FieldError, ...] = ()
    result: CalculationResult | None = None
    messages: tuple[Message, ...] = ()
    pending: PendingOperation | None = None
    next_message_id: int = 1
    import_error: str | None = None
    """Proč se poslední soubor nepodařilo načíst (UC-06 E1); zakázka zůstala beze změny."""
    saved_inputs: ChangeProposal | None = None
    """Otisk vstupů naposledy uloženého nebo načteného souboru (`inputs_fingerprint`)."""
    proposal_start: ChangeProposal | None = None
    """Otisk ručního návrhu v okamžiku, kdy vznikl; netknutý formulář není rozpracovaná práce."""


def initial_state(session_id: str) -> AppState:
    """Prázdná relace; `session_id` dodá aplikační vrstva (jádro nečte náhodu)."""
    return AppState(session_id=session_id)


class Step(StrEnum):
    """Krok pracovní plochy (service design F0)."""

    INPUT = "input"
    REVIEW = "review"
    RESULT = "result"


def current_step(state: AppState) -> Step:
    """Krok podle stavu: čekající návrh → kontrola, potvrzená zakázka → plán a cena."""
    if state.proposal is not None:
        return Step.REVIEW
    if state.project is not None:
        return Step.RESULT
    return Step.INPUT


def is_result_stale(state: AppState) -> bool:
    """Plán je neaktuální, když se od výpočtu změnily vstupy plánu (R3).

    Čekající návrh dělá plán neaktuálním, jen když se jeho vstupy od výpočtu liší;
    pouhé otevření úpravy bez změny plán nezneplatní.
    """
    if state.result is None:
        return False
    source = state.result.source
    if state.proposal is not None and _draft_plan_inputs(state.proposal) != _draft_plan_inputs(
        proposal_from_project(source)
    ):
        return True
    current = state.project
    return current is None or _plan_inputs(state.result.source) != _plan_inputs(current)


def _plan_inputs(project: Project) -> object:
    """Vstupy plánu; ceny skladových délek jen při cíli „nejnižší cena“."""
    stock = project.problem.stock
    if project.parameters.objective is not Objective.CHEAPEST:
        stock = tuple(item.model_copy(update={"price": None}) for item in stock)
    return (project.problem.parts, stock, project.parameters)


def _draft_plan_inputs(proposal: ChangeProposal) -> object:
    """Vstupy plánu z návrhu; ceny jen při cíli „nejnižší cena“ (jako `_plan_inputs`)."""
    stock = proposal.stock
    if proposal.parameters.objective is not Objective.CHEAPEST:
        stock = tuple(item.model_copy(update={"price": None}) for item in stock)
    return (proposal.parts, stock, proposal.parameters)


def has_unsaved_changes(state: AppState) -> bool:
    """Neuložené změny (UC-15): zakázka se liší od posledního souboru, nebo čeká návrh s prací."""
    if state.project is not None:
        current = inputs_fingerprint(proposal_from_project(state.project))
        if current != state.saved_inputs:
            return True
    proposal = state.proposal
    if proposal is None:
        return False
    return state.proposal_start is None or inputs_fingerprint(proposal) != state.proposal_start
