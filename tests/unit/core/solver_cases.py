"""Stavba malých zakázek 1D pro testy solveru a validátoru."""

from decimal import Decimal

from decision_engine.core.model.cutting_1d import (
    Objective,
    Parameters,
    Part,
    Problem,
    Project,
    StockLength,
)


def project_1d(
    parts: list[tuple[int, int]],
    stock: list[tuple[int, str | None]],
    *,
    kerf: int = 0,
    trim: int = 0,
    min_remnant: int = 300,
    objective: Objective = Objective.LEAST_MATERIAL,
) -> Project:
    """Zakázka z dvojic (délka, počet) a (délka tyče, cena)."""
    return Project(
        id="z",
        name="Test",
        format_version=1,
        task_type="cutting_1d",
        revision=0,
        problem=Problem(
            material=None,
            parts=tuple(
                Part(id=f"p{i}", name=f"díl {i}", length_mm=length, quantity=quantity)
                for i, (length, quantity) in enumerate(parts, start=1)
            ),
            stock=tuple(
                StockLength(
                    id=f"s{i}",
                    length_mm=length,
                    price=Decimal(price) if price is not None else None,
                )
                for i, (length, price) in enumerate(stock, start=1)
            ),
        ),
        parameters=Parameters(
            kerf_mm=kerf, trim_mm=trim, min_remnant_mm=min_remnant, objective=objective
        ),
    )
