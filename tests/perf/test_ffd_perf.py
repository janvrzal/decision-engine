"""Výkon FFD na demo sadě kolem 100 kusů (spec kap. 8: cíl do 10 s). Marker `slow`."""

import time
from decimal import Decimal

import pytest

from decision_engine.core.model.cutting_1d import (
    Objective,
    Parameters,
    Part,
    Problem,
    Project,
    StockLength,
)
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.validation.check_cutting_1d import check_cutting_1d

pytestmark = pytest.mark.slow

LIMIT_SECONDS = 10.0


@pytest.mark.parametrize("objective", list(Objective))
def test_sto_kusu_do_deseti_sekund(objective: Objective) -> None:
    lengths = [2350, 1875, 1240, 980, 760, 615, 480, 2990, 1430, 355]
    project = Project(
        id="demo",
        name="Demo 100 kusů",
        format_version=1,
        task_type="cutting_1d",
        revision=0,
        problem=Problem(
            material=None,
            parts=tuple(
                Part(id=f"p{i}", name=f"díl {i}", length_mm=length, quantity=10)
                for i, length in enumerate(lengths)
            ),
            stock=(
                StockLength(id="s1", length_mm=6000, price=Decimal("420")),
                StockLength(id="s2", length_mm=4000, price=Decimal("290")),
            ),
        ),
        parameters=Parameters(
            kerf_mm=Decimal(3), trim_mm=Decimal(5), min_remnant_mm=300, objective=objective
        ),
    )

    start = time.perf_counter()
    result = solve_ffd(project)
    elapsed = time.perf_counter() - start

    print(f"FFD, 100 kusů, cíl {objective.value}: {elapsed * 1000:.1f} ms, tyčí {len(result.bars)}")
    assert check_cutting_1d(project, result) == ()
    assert elapsed < LIMIT_SECONDS


def test_nejvetsi_povolena_zakazka_do_limitu() -> None:
    """5 000 kusů (spec kap. 8, horní mez zakázky) se spočítá výrazně pod 10 s."""
    lengths = [2350, 1875, 1240, 980, 760]
    project = Project(
        id="max",
        name="Největší zakázka",
        format_version=1,
        task_type="cutting_1d",
        revision=0,
        problem=Problem(
            material=None,
            parts=tuple(
                Part(id=f"p{i}", name=f"díl {i}", length_mm=length, quantity=1_000)
                for i, length in enumerate(lengths)
            ),
            stock=(
                StockLength(id="s1", length_mm=6000, price=Decimal("420")),
                StockLength(id="s2", length_mm=4000, price=Decimal("290")),
            ),
        ),
        parameters=Parameters(
            kerf_mm=Decimal(3), trim_mm=Decimal(5), min_remnant_mm=300, objective=Objective.CHEAPEST
        ),
    )

    start = time.perf_counter()
    result = solve_ffd(project)
    elapsed = time.perf_counter() - start

    assert check_cutting_1d(project, result) == ()
    assert elapsed < LIMIT_SECONDS
