"""Události: všechno, co se v relaci může stát (ADR-0006).

Události od uživatele posílá frontend, ostatní vrací aplikační vrstva jako výsledek efektů.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import MAX_PARTS, MAX_STOCK
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)
from decision_engine.core.state import AiErrorKind

MAX_MESSAGE_CHARS = 4_000
"""Nejdelší zpráva do dialogu; delší text by jen prodražil volání modelu."""


class _Event(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MessageSent(_Event):
    """Uživatel odeslal zprávu nebo zadání."""

    type: Literal["MessageSent"] = "MessageSent"
    text: Annotated[str, Field(max_length=MAX_MESSAGE_CHARS)]


class ToolSelected(_Event):
    """Uživatel zvolil nástroj ručně (karta nástroje, „Zadat ručně“; UC-13)."""

    type: Literal["ToolSelected"] = "ToolSelected"
    capability: Literal["cutting_1d"]


class EditRequested(_Event):
    """Uživatel chce ručně upravit potvrzenou zakázku („Upravit údaje“)."""

    type: Literal["EditRequested"] = "EditRequested"


class ProjectImported(_Event):
    """Uživatel načetl soubor zakázky (UC-06); obsah se ověří v jádře."""

    type: Literal["ProjectImported"] = "ProjectImported"
    content: str = Field(max_length=1_000_000)
    discard_unsaved: bool = False
    """Uživatel potvrdil zahození neuložené práce; jinak se neuložená práce nezahodí."""


class ProjectSaved(_Event):
    """Uživatel si stáhl soubor zakázky v dané revizi (UC-06)."""

    type: Literal["ProjectSaved"] = "ProjectSaved"
    revision: int


class NewProjectRequested(_Event):
    """Uživatel začíná novou zakázku; rozpracovaná se zahodí (UC-15).

    Na neuložené změny se ptá UI předem. Reducer neuloženou práci zahodí jen
    s `discard_unsaved`: UI mohlo vycházet ze zastaralého stavu (druhá karta prohlížeče).
    """

    type: Literal["NewProjectRequested"] = "NewProjectRequested"
    discard_unsaved: bool = False


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
    parts: Annotated[tuple[PartDraft, ...], Field(max_length=MAX_PARTS)]
    stock: Annotated[tuple[StockLengthDraft, ...], Field(max_length=MAX_STOCK)]
    parameters: ParametersDraft
    confirmed: Annotated[tuple[str, ...], Field(max_length=MAX_PARTS * 3)] = ()
    """Buňky, které uživatel v této úpravě sám vyplnil (`parts.0.length_mm`, `objective`);
    ručně zadaná hodnota je potvrzená, i když se rovná výchozí (R6)."""


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
    | ProjectImported
    | ProjectSaved
    | NewProjectRequested
    | ProposalReceived
    | ProposalEdited
    | ProposalConfirmed
    | ProposalRejected
    | SolveRequested
    | SolveFinished
    | AiFailed
)
