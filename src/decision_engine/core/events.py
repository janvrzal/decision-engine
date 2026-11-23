"""Události: všechno, co se v relaci může stát (ADR-0006).

Události od uživatele posílá frontend, ostatní vrací aplikační vrstva jako výsledek efektů.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)
from decision_engine.core.state import AiErrorKind


class _Event(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MessageSent(_Event):
    """Uživatel odeslal zprávu nebo zadání."""

    type: Literal["MessageSent"] = "MessageSent"
    text: str


class ToolSelected(_Event):
    """Uživatel zvolil nástroj ručně (karta nástroje, „Zadat ručně“; UC-13)."""

    type: Literal["ToolSelected"] = "ToolSelected"
    capability: Literal["cutting_1d"]


class EditRequested(_Event):
    """Uživatel chce ručně upravit potvrzenou zakázku („Upravit údaje“)."""

    type: Literal["EditRequested"] = "EditRequested"


class ProposalReceived(_Event):
    """Extrakce vrátila návrh změny (výsledek `CallExtractor`)."""

    type: Literal["ProposalReceived"] = "ProposalReceived"
    proposal: ChangeProposal
    reply: str = ""
    """Krátká odpověď asistenta do Panelu Dialog."""


class ProposalEdited(_Event):
    """Uživatel upravil návrh v kontrolní tabulce (celý nový obsah návrhu)."""

    type: Literal["ProposalEdited"] = "ProposalEdited"
    name: str | None
    material: str | None
    parts: tuple[PartDraft, ...]
    stock: tuple[StockLengthDraft, ...]
    parameters: ParametersDraft


class ProposalConfirmed(_Event):
    """Uživatel klikl na „Potvrdit a vypočítat“."""

    type: Literal["ProposalConfirmed"] = "ProposalConfirmed"


class ProposalRejected(_Event):
    """Uživatel návrh zahodil („Zahodit změny“)."""

    type: Literal["ProposalRejected"] = "ProposalRejected"


class SolveRequested(_Event):
    """Uživatel chce plán spočítat znovu („Přepočítat“)."""

    type: Literal["SolveRequested"] = "SolveRequested"


class SolveFinished(_Event):
    """Solver dokončil výpočet (výsledek `RunSolver`)."""

    type: Literal["SolveFinished"] = "SolveFinished"
    result: CalculationResult


class AiFailed(_Event):
    """Volání AI selhalo."""

    type: Literal["AiFailed"] = "AiFailed"
    kind: AiErrorKind


type Event = (
    MessageSent
    | ToolSelected
    | EditRequested
    | ProposalReceived
    | ProposalEdited
    | ProposalConfirmed
    | ProposalRejected
    | SolveRequested
    | SolveFinished
    | AiFailed
)
