"""Návrh změny zakázky (`ChangeProposal`): co navrhla AI nebo uživatel, ale ještě neplatí.

Návrh unese i neúplná data (chybějící skladová délka, prázdná buňka), proto má vlastní
typy s volitelnými hodnotami. Platnost se ověří až při potvrzení přes `parse_project`,
takže pravidla validace jsou na jednom místě (spec kap. 7 Stav zakázky, R1, R6).
"""

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.errors import FieldError, FieldPath
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.result import Result
from decision_engine.core.validation.cutting_1d import parse_project


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PartDraft(_Frozen):
    id: str
    name: str | None = None
    length_mm: int | None = None
    quantity: int | None = None


class StockLengthDraft(_Frozen):
    id: str
    length_mm: int | None = None
    price: Decimal | None = None


class ParametersDraft(_Frozen):
    kerf_mm: int | None = None
    trim_mm: int | None = None
    min_remnant_mm: int | None = None
    objective: Objective | None = None
    time_limit_s: int | None = None


class ChangeProposal(_Frozen):
    """Rozpracovaná podoba vstupů plánu čekající na potvrzení uživatelem."""

    base_revision: int | None
    """Revize, proti které návrh vznikl; `None` u nové zakázky."""
    name: str | None = None
    material: str | None = None
    parts: tuple[PartDraft, ...] = ()
    stock: tuple[StockLengthDraft, ...] = ()
    parameters: ParametersDraft = ParametersDraft()
    unconfirmed: frozenset[FieldPath] = frozenset()
    """Hodnoty z výchozího nastavení nebo odhadnuté modelem (R6); UI je označí."""
    origin: Literal["ai", "manual", "file"] = "ai"
    """Odkud návrh je: extrakce z textu, ruční zadání nebo úprava (UC-13), soubor (UC-06)."""


def proposal_from_project(project: Project) -> ChangeProposal:
    """Návrh pro ruční úpravu potvrzené zakázky: stejné hodnoty i id, nic nepotvrzeného."""
    problem = project.problem
    return ChangeProposal(
        base_revision=project.revision,
        name=project.name,
        material=problem.material,
        parts=tuple(
            PartDraft(id=p.id, name=p.name, length_mm=p.length_mm, quantity=p.quantity)
            for p in problem.parts
        ),
        stock=tuple(
            StockLengthDraft(id=s.id, length_mm=s.length_mm, price=s.price) for s in problem.stock
        ),
        parameters=ParametersDraft(**project.parameters.model_dump()),
        origin="manual",
    )


def inputs_fingerprint(proposal: ChangeProposal) -> ChangeProposal:
    """Jen hodnoty vstupů návrhu, bez původu a označení; pro porovnání „změnilo se něco?“."""
    return proposal.model_copy(
        update={"base_revision": None, "origin": "manual", "unconfirmed": frozenset()}
    )


def confirm_proposal(
    proposal: ChangeProposal, project_id: str, revision: int
) -> Result[Project, tuple[FieldError, ...]]:
    """Složí z návrhu novou revizi zakázky, nebo vrátí chyby po polích."""
    return parse_project(
        {
            "id": project_id,
            "format_version": 1,
            "task_type": "cutting_1d",
            "revision": revision,
            **_present({"name": proposal.name}),
            "problem": {
                "material": proposal.material,
                "parts": [_present(part.model_dump()) for part in proposal.parts],
                "stock": [_stock(stock) for stock in proposal.stock],
            },
            "parameters": _present(proposal.parameters.model_dump()),
        }
    )


def _present(values: dict[str, Any]) -> dict[str, Any]:
    """Vynechá chybějící hodnoty, aby validace hlásila „Chybí hodnota“, ne chybný typ."""
    return {key: value for key, value in values.items() if value is not None}


def _stock(stock: StockLengthDraft) -> dict[str, Any]:
    # Chybějící cena je platný stav (cena chybí), proto se nevynechává.
    return {**_present(stock.model_dump()), "price": stock.price}
