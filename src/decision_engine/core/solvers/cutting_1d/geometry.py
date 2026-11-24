"""Geometrie jedné tyče podle UC-01: kde začíná další kus a co zbude na konci.

První kus začíná na zarovnávacím ořezu, každý další o prořez za koncem předchozího.
Kus se vejde, když jeho konec nepřesáhne délku tyče (⇔ Σl + n·k ≤ L + k - ořez).
Za posledním kusem: zbytek `r` ≤ prořez spotřebuje řez; jinak úsek `r - prořez`
je využitelný zbytek (≥ minimální délka), nebo odpad.
"""

from collections.abc import Sequence
from decimal import Decimal
from typing import Literal

from decision_engine.core.model.calculation import PlacedPiece
from decision_engine.core.model.cutting_1d import Parameters

type RemainderKind = Literal["none", "remnant", "waste"]


def next_start(pieces: Sequence[PlacedPiece], parameters: Parameters) -> Decimal:
    """Poloha, na které začne další kus."""
    if not pieces:
        return parameters.trim_mm
    last = pieces[-1]
    return last.start_mm + last.length_mm + parameters.kerf_mm


def fits(
    bar_length_mm: int, pieces: Sequence[PlacedPiece], length_mm: int, parameters: Parameters
) -> bool:
    """Vejde se kus dané délky za kusy, které už na tyči jsou?"""
    return next_start(pieces, parameters) + length_mm <= bar_length_mm


def remainder(
    bar_length_mm: int, pieces: Sequence[PlacedPiece], parameters: Parameters
) -> tuple[RemainderKind, Decimal]:
    """Druh a délka úseku za posledním kusem (bez prořezu, který ho oddělí)."""
    end = pieces[-1].start_mm + pieces[-1].length_mm if pieces else parameters.trim_mm
    rest = bar_length_mm - end
    if rest <= parameters.kerf_mm:
        return "none", Decimal(0)
    length = rest - parameters.kerf_mm
    return ("remnant" if length >= parameters.min_remnant_mm else "waste"), length
