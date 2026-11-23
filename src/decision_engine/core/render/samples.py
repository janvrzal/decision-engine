"""Ukázkové zakázky pro vizuální kontrolu a snapshoty plánu (bez I/O)."""

from decimal import Decimal

from decision_engine.core.model.cutting_1d import (
    Objective,
    Parameters,
    Part,
    Problem,
    Project,
    StockLength,
)


def _project(
    name: str,
    parts: list[tuple[str, int, int]],
    stock: list[tuple[int, str]],
    parameters: Parameters,
) -> Project:
    return Project(
        id=name,
        name=name,
        format_version=1,
        task_type="cutting_1d",
        revision=0,
        problem=Problem(
            material="jekl 40×40×2",
            parts=tuple(
                Part(id=f"p{i}", name=label, length_mm=length, quantity=quantity)
                for i, (label, length, quantity) in enumerate(parts, start=1)
            ),
            stock=tuple(
                StockLength(id=f"s{i}", length_mm=length, price=Decimal(price))
                for i, (length, price) in enumerate(stock, start=1)
            ),
        ),
        parameters=parameters,
    )


SAMPLES: dict[str, Project] = {
    "jekly-a-pricky": _project(
        "jekly-a-pricky",
        [("jekl", 2000, 10), ("příčka", 1500, 5)],
        [(6000, "420")],
        Parameters(kerf_mm=3, trim_mm=0, min_remnant_mm=300, objective=Objective.CHEAPEST),
    ),
    "regal-vice-delek": _project(
        "regal-vice-delek",
        [
            ("noha", 1800, 4),
            ("polička", 1200, 8),
            ("hloubka", 400, 8),
            ("vzpěra", 950, 4),
            ("příčka", 760, 6),
            ("lišta", 615, 3),
            ("držák", 220, 6),
            ("úchyt", 140, 4),
            ("distanční díl", 90, 6),
        ],
        [(6000, "420"), (3000, "230")],
        Parameters(kerf_mm=3, trim_mm=10, min_remnant_mm=500, objective=Objective.LEAST_MATERIAL),
    ),
    "castecny": _project(
        "castecny",
        [("nosník", 6500, 1), ("sloupek", 2400, 3)],
        [(6000, "420")],
        Parameters(kerf_mm=3, trim_mm=0, min_remnant_mm=300, objective=Objective.FEWEST_BARS),
    ),
}
"""Jedna délka se zbytky; více délek s ořezem, odpadem a 9 typy dílů; částečný plán."""
