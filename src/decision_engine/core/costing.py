"""Orientační cena materiálu (UC-04, první etapa): spotřebované tyče × cena za kus.

Čistá funkce nad výsledkem výpočtu. Chybí-li cena některé spotřebované skladové délky,
kalkulace je neúplná a součet se neuvádí (spec UC-04: chybějící cena není nula).
Práce, přirážka a DPH přibudou v další etapě.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.calculation import CalculationResult


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class MaterialLine(_Frozen):
    """Jedna spotřebovaná skladová délka: kolik kusů a za kolik."""

    stock_id: str
    length_mm: int
    count: int
    unit_price: Decimal | None
    total: Decimal | None
    """`count × unit_price`; `None`, když cena chybí."""


class MaterialCost(_Frozen):
    lines: tuple[MaterialLine, ...]
    total: Decimal | None
    """Součet všech řádků; `None`, když některé ceně chybí (neúplná kalkulace)."""
    missing_price: bool


def material_cost(result: CalculationResult) -> MaterialCost:
    """Cena spotřebovaných tyčí podle skladových délek zakázky, ze které výsledek vznikl."""
    lines = tuple(
        MaterialLine(
            stock_id=stock.id,
            length_mm=stock.length_mm,
            count=count,
            unit_price=stock.price,
            total=None if stock.price is None else stock.price * count,
        )
        for stock in result.source.problem.stock
        if (count := sum(1 for bar in result.bars if bar.stock_id == stock.id)) > 0
    )
    missing = any(line.total is None for line in lines)
    total = None if missing else sum((line.total or Decimal(0) for line in lines), Decimal(0))
    return MaterialCost(lines=lines, total=total, missing_price=missing)
