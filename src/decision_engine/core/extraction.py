"""Výstup extrakce z modelu a jeho převod na návrh změny (spec kap. 6, UC-01, R6).

Model vrací `ExtractionOutput`; nic z něj neplatí, dokud uživatel návrh nepotvrdí.
Výchozí hodnoty doplňuje kód podle specifikace, ne model, a označí je jako nepotvrzené.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from decision_engine.core.errors import FieldPath
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)

DEFAULT_STOCK_LENGTH_MM = 6000
"""Nabídnutá skladová délka, když zadání žádnou neuvádí (UC-01 A2)."""
DEFAULT_MIN_REMNANT_MM = 300
"""Výchozí minimální délka využitelného zbytku (spec UC-01, plan-rezani.md)."""
DEFAULT_TRIM_MM = 0
"""Zarovnávací ořez je volitelný; bez zmínky v zadání se nepoužije."""
DEFAULT_PROJECT_NAME = "Nová zakázka"
"""Název, když ho extrakce nenajde (mapa obrazovek, Hlavička zakázky)."""


class _Output(BaseModel):
    # Model občas přidá pole navíc; nevadí, použije se jen to, co schéma zná.
    model_config = ConfigDict(frozen=True, extra="ignore")


class ExtractedPart(_Output):
    ref: str | None = Field(None, description="id dílu z potvrzené zakázky, pokud jde o úpravu")
    name: str | None = Field(None, description="název dílu tak, jak ho uživatel nazval")
    length_mm: int | None = Field(None, description="délka jednoho kusu v milimetrech")
    quantity: int | None = Field(None, description="počet kusů")
    uncertain: tuple[str, ...] = Field(
        (), description="pole, která jsi musel odhadnout (např. length_mm)"
    )


class ExtractedStock(_Output):
    ref: str | None = Field(None, description="id skladové délky z potvrzené zakázky")
    length_mm: int | None = Field(None, description="délka tyče v milimetrech")
    price: Decimal | None = Field(None, description="cena za jednu tyč v Kč, pokud je uvedena")
    uncertain: tuple[str, ...] = ()


class ExtractionOutput(_Output):
    """Co model ze zadání vyčetl. Chybějící údaje jsou `null`, nevymýšlí se."""

    name: str | None = Field(None, description="krátký název zakázky")
    material: str | None = Field(None, description="materiál nebo profil, např. jekl 40×40×2")
    parts: tuple[ExtractedPart, ...] = ()
    stock: tuple[ExtractedStock, ...] = ()
    kerf_mm: int | None = Field(None, description="prořez v milimetrech, jen pokud je uveden")
    trim_mm: int | None = Field(None, description="zarovnávací ořez v mm, jen pokud je uveden")
    min_remnant_mm: int | None = Field(None, description="minimální využitelný zbytek v mm")
    objective: Objective | None = Field(None, description="cíl, jen pokud ho uživatel řekl")
    reply: str = Field("", description="jedna až dvě věty pro uživatele česky")


def proposal_from_extraction(output: ExtractionOutput, base: Project | None) -> ChangeProposal:
    """Převede výstup modelu na návrh změny proti `base` (nebo nové zakázce)."""
    unconfirmed: set[FieldPath] = set()

    part_ids = _ids(
        [part.ref for part in output.parts],
        {part.id for part in base.problem.parts} if base else set(),
        "p",
    )
    parts = tuple(
        PartDraft(
            id=part_id,
            name=part.name,
            length_mm=part.length_mm,
            quantity=part.quantity,
        )
        for part_id, part in zip(part_ids, output.parts, strict=True)
    )
    for index, part in enumerate(output.parts):
        unconfirmed |= {("problem", "parts", index, field) for field in part.uncertain}

    stock_ids = _ids(
        [stock.ref for stock in output.stock],
        {stock.id for stock in base.problem.stock} if base else set(),
        "s",
    )
    stock = tuple(
        StockLengthDraft(id=stock_id, length_mm=item.length_mm, price=item.price)
        for stock_id, item in zip(stock_ids, output.stock, strict=True)
    )
    for index, item in enumerate(output.stock):
        unconfirmed |= {("problem", "stock", index, field) for field in item.uncertain}
    if not stock and base is not None:
        stock = tuple(
            StockLengthDraft(id=item.id, length_mm=item.length_mm, price=item.price)
            for item in base.problem.stock
        )
    if not stock:
        stock = (StockLengthDraft(id="s1", length_mm=DEFAULT_STOCK_LENGTH_MM),)
        unconfirmed.add(("problem", "stock", 0, "length_mm"))

    parameters, defaulted = _parameters(output, stock, base)
    unconfirmed |= {("parameters", field) for field in defaulted}

    return ChangeProposal(
        base_revision=base.revision if base else None,
        name=output.name or (base.name if base else DEFAULT_PROJECT_NAME),
        # Navazující změna mění jen to, co uživatel řekl (UC-03): co model nezopakoval,
        # zůstane z potvrzené revize.
        material=output.material or (base.problem.material if base else None),
        parts=parts,
        stock=stock,
        parameters=parameters,
        unconfirmed=frozenset(unconfirmed),
    )


def _parameters(
    output: ExtractionOutput, stock: tuple[StockLengthDraft, ...], base: Project | None
) -> tuple[ParametersDraft, set[str]]:
    """Parametry ze zadání; chybějící převezme z potvrzené revize, jinak z výchozích hodnot.

    Vrátí i seznam parametrů doplněných výchozí hodnotou; převzaté z revize už uživatel
    potvrdil, proto nepotvrzené nejsou.
    """
    if base is not None:
        kept = base.parameters
        return (
            ParametersDraft(
                kerf_mm=output.kerf_mm if output.kerf_mm is not None else kept.kerf_mm,
                trim_mm=output.trim_mm if output.trim_mm is not None else kept.trim_mm,
                min_remnant_mm=(
                    output.min_remnant_mm
                    if output.min_remnant_mm is not None
                    else kept.min_remnant_mm
                ),
                objective=output.objective or kept.objective,
                time_limit_s=kept.time_limit_s,
            ),
            set(),
        )
    defaulted: set[str] = set()
    trim = output.trim_mm
    if trim is None:
        trim = DEFAULT_TRIM_MM
        defaulted.add("trim_mm")
    min_remnant = output.min_remnant_mm
    if min_remnant is None:
        min_remnant = DEFAULT_MIN_REMNANT_MM
        defaulted.add("min_remnant_mm")
    objective = output.objective
    if objective is None:
        # Spec UC-01: nejnižší cena, jsou-li ceny všech délek, jinak nejméně materiálu.
        all_priced = all(item.price is not None for item in stock)
        objective = Objective.CHEAPEST if all_priced else Objective.LEAST_MATERIAL
        defaulted.add("objective")
    # Prořez nemá ve specifikaci výchozí hodnotu: chybí-li, uživatel ho doplní.
    return (
        ParametersDraft(
            kerf_mm=output.kerf_mm,
            trim_mm=trim,
            min_remnant_mm=min_remnant,
            objective=objective,
        ),
        defaulted,
    )


def _ids(refs: list[str | None], existing: set[str], prefix: str) -> list[str]:
    """Ponechá známá `id` (úprava), ostatním přidělí nová, která s ničím nekolidují."""
    taken = set(existing)
    result: list[str] = []
    counter = 1
    for ref in refs:
        if ref is not None and ref in existing and ref not in result:
            result.append(ref)
            continue
        while f"{prefix}{counter}" in taken or f"{prefix}{counter}" in result:
            counter += 1
        new_id = f"{prefix}{counter}"
        taken.add(new_id)
        result.append(new_id)
    return result


def empty_proposal() -> ChangeProposal:
    """Prázdný návrh pro ruční zadání (UC-13): stejné výchozí hodnoty jako cesta přes AI."""
    proposal = proposal_from_extraction(ExtractionOutput.model_validate({}), None)
    return proposal.model_copy(update={"origin": "manual"})
