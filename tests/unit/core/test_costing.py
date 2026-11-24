"""Orientační cena materiálu (UC-04, první etapa)."""

from decimal import Decimal

from solver_cases import project_1d

from decision_engine.core.costing import material_cost
from decision_engine.core.model.cutting_1d import Objective
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd


def test_cena_je_pocet_tyci_krat_cena_za_kus() -> None:
    project = project_1d([(1800, 4), (1200, 8)], [(6000, "320.50")], kerf=3)
    result = solve_ffd(project)

    cost = material_cost(result)

    (line,) = cost.lines
    assert line.count == len(result.bars)
    assert line.total == Decimal("320.50") * len(result.bars)
    assert cost.total == line.total
    assert not cost.missing_price


def test_vice_delek_rozlisi_pouzitou_polozku() -> None:
    project = project_1d(
        [(2500, 3), (1000, 2)],
        [(6000, "320"), (3000, "150")],
        objective=Objective.CHEAPEST,
    )

    cost = material_cost(solve_ffd(project))

    assert cost.total == sum((line.total or Decimal(0) for line in cost.lines), Decimal(0))
    assert {line.stock_id for line in cost.lines} <= {"s1", "s2"}


def test_chybejici_cena_neni_nula() -> None:
    project = project_1d([(1800, 4)], [(6000, None)])

    cost = material_cost(solve_ffd(project))

    assert cost.missing_price
    assert cost.total is None
    assert cost.lines[0].total is None


def test_bez_tyci_je_cena_nula_a_uplna() -> None:
    project = project_1d([(7000, 1)], [(6000, "320")])

    cost = material_cost(solve_ffd(project))

    assert cost.lines == ()
    assert cost.total == Decimal(0)
