"""Výsledek výpočtu plánu (spec kap. 7 `CalculationResult`, kap. 4 Výsledek).

Délky dílů a tyčí jsou `int` v milimetrech (ADR-0002); polohy a zbytky závisí na prořezu
a ořezu, proto jsou `Decimal` s nejvýš jedním desetinným místem (ADR-0011). Jen výtěžnost
je poměr (`float`).
"""

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.cutting_1d import Project


class SolutionStatus(StrEnum):
    """Stav plánu (spec kap. 4): „Optimální“ jen při prokázaném optimu (AGENTS.md pravidlo 9)."""

    OPTIMAL = "optimal"
    BEST_FOUND = "best_found"
    PARTIAL = "partial"
    INFEASIBLE = "infeasible"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PlacedPiece(_Frozen):
    """Jeden umístěný kus dílu na tyči."""

    part_id: str
    length_mm: int
    start_mm: Decimal
    """Poloha začátku kusu od začátku tyče (plan-rezani.md: polohy řezů od začátku tyče)."""


class Bar(_Frozen):
    """Jedna spotřebovaná skladová tyč a kusy na ní v pořadí řezání."""

    stock_id: str
    length_mm: int
    pieces: tuple[PlacedPiece, ...]


class UnplacedPiece(_Frozen):
    """Kusy dílu, které plán neobsahuje, a proč (UC-01 A4)."""

    part_id: str
    quantity: int
    reason: Literal["too_long"]


class Metrics(_Frozen):
    """Souhrn plánu (spec kap. 4 Výsledek)."""

    bars_used: int
    bars_by_stock: tuple[tuple[str, int], ...]
    """Počet spotřebovaných tyčí podle `stock_id`, v pořadí skladových délek zakázky."""
    parts_length_mm: int
    consumed_length_mm: int
    remnant_length_mm: Decimal
    remnant_count: int
    waste_length_mm: Decimal
    """Spotřebovaná délka bez dílů a využitelných zbytků (obsahuje prořezy a ořezy)."""
    yield_ratio: float
    """Délka dílů / spotřebovaná délka; 0 bez spotřebovaných tyčí."""


class CalculationResult(_Frozen):
    """Výsledek výpočtu nesoucí revizi zakázky, ze které vznikl."""

    status: SolutionStatus
    source: Project
    """Potvrzená revize zakázky, ze které výsledek vznikl (pro odvození neaktuálnosti)."""
    bars: tuple[Bar, ...]
    unplaced: tuple[UnplacedPiece, ...]
    metrics: Metrics
    lower_bound: Decimal | None = None
    """Dolní mez hodnoty cíle (tyče, mm nebo Kč podle cíle), zaokrouhlená nahoru na jednotku.

    „Optimální“ smí plán být, jen když hodnota cíle mez dosáhne (pravidlo 9)."""
