"""Ručně spočítané příklady FFD 1D (skill `overeni-solveru`). Každý výsledek projde validátorem."""

import pytest
from solver_cases import project_1d

from decision_engine.core.model.calculation import CalculationResult, SolutionStatus
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.validation.check_cutting_1d import check_cutting_1d


def _solve(project: Project) -> CalculationResult:
    result = solve_ffd(project)
    assert check_cutting_1d(project, result) == ()
    return result


def _layout(result: CalculationResult) -> list[list[tuple[str, int]]]:
    """Tyče jako seznam (díl, poloha začátku)."""
    return [[(p.part_id, p.start_mm) for p in bar.pieces] for bar in result.bars]


def test_prorez_se_pocita_mezi_kusy() -> None:
    # 3 × 2000 + 2 × 3 = 6006 > 6000: třetí kus se nevejde.
    result = _solve(project_1d([(2000, 3)], [(6000, None)], kerf=3))

    assert _layout(result) == [[("p1", 0), ("p1", 2003)], [("p1", 0)]]
    metrics = result.metrics
    assert metrics.bars_used == 2
    assert metrics.consumed_length_mm == 12_000
    assert metrics.parts_length_mm == 6000
    # Zbytky: 6000 - 4003 - 3 = 1994 a 6000 - 2000 - 3 = 3997, oba ≥ 300.
    assert metrics.remnant_count == 2
    assert metrics.remnant_length_mm == 1994 + 3997
    assert metrics.waste_length_mm == 12_000 - 6000 - 1994 - 3997  # tři prořezy
    assert result.status is SolutionStatus.BEST_FOUND


def test_bez_prorezu_se_kusy_vejdou_presne() -> None:
    result = _solve(project_1d([(2000, 3)], [(6000, None)], kerf=0))

    assert _layout(result) == [[("p1", 0), ("p1", 2000), ("p1", 4000)]]
    assert result.metrics.waste_length_mm == 0
    assert result.metrics.yield_ratio == 1.0


def test_kus_presne_na_delku_tyce() -> None:
    result = _solve(project_1d([(6000, 1)], [(6000, None)], kerf=3))

    assert result.metrics.bars_used == 1
    assert result.metrics.remnant_count == 0
    assert result.metrics.waste_length_mm == 0


def test_zarovnavaci_orez_posune_prvni_kus() -> None:
    result = _solve(project_1d([(5990, 1)], [(6000, None)], trim=10))

    assert _layout(result) == [[("p1", 10)]]


def test_kus_delsi_nez_tyc_po_orezu_je_neumisteny() -> None:
    result = _solve(project_1d([(5991, 1), (1000, 2)], [(6000, None)], trim=10))

    assert result.status is SolutionStatus.PARTIAL
    assert [(u.part_id, u.quantity, u.reason) for u in result.unplaced] == [("p1", 1, "too_long")]
    assert result.metrics.parts_length_mm == 2000


def test_vse_prilis_dlouhe_je_bez_reseni() -> None:
    result = _solve(project_1d([(7000, 2)], [(6000, None)]))

    assert result.status is SolutionStatus.INFEASIBLE
    assert result.bars == ()
    assert result.metrics.yield_ratio == 0.0


@pytest.mark.parametrize(("piece", "remnants", "waste"), [(700, 1, 0), (701, 0, 299)])
def test_zbytek_na_prahu_je_vyuzitelny(piece: int, remnants: int, waste: int) -> None:
    result = _solve(project_1d([(piece, 1)], [(1000, None)], min_remnant=300))

    assert result.metrics.remnant_count == remnants
    assert result.metrics.waste_length_mm == waste


def test_zbytek_kratsi_nez_prorez_spotrebuje_rez() -> None:
    result = _solve(project_1d([(998, 1)], [(1000, None)], kerf=3))

    assert result.metrics.remnant_count == 0
    assert result.metrics.waste_length_mm == 2


@pytest.mark.parametrize(
    ("objective", "stocks"),
    [
        # Tři kusy 1 900 mm: tyč 6 000 pojme tři, tyč 3 000 jeden.
        (Objective.CHEAPEST, ["s2", "s2", "s2"]),  # 3 × 100 Kč < 400 Kč
        (Objective.LEAST_MATERIAL, ["s1"]),  # 6 000 mm < 9 000 mm
        (Objective.FEWEST_BARS, ["s1"]),
    ],
)
def test_vyber_skladove_delky_podle_cile(objective: Objective, stocks: list[str]) -> None:
    project = project_1d([(1900, 3)], [(6000, "400"), (3000, "100")], objective=objective)

    result = _solve(project)

    assert [bar.stock_id for bar in result.bars] == stocks


def test_kus_ktery_se_vejde_jen_do_delsi_tyce() -> None:
    project = project_1d([(4000, 1), (1000, 1)], [(3000, "100"), (6000, "400")])

    result = _solve(project)

    assert [bar.stock_id for bar in result.bars] == ["s2"]
    assert result.metrics.bars_by_stock == (("s2", 1),)


def test_dily_stejne_delky_si_drzi_identitu() -> None:
    result = _solve(project_1d([(1000, 2), (1000, 1)], [(6000, None)]))

    ids = [p.part_id for bar in result.bars for p in bar.pieces]
    assert sorted(ids) == ["p1", "p1", "p2"]


def test_vypocet_je_deterministicky() -> None:
    project = project_1d([(1234, 7), (567, 11), (2890, 3)], [(6000, "350"), (4000, "260")], kerf=3)

    assert solve_ffd(project) == solve_ffd(project)


def test_nikdy_nevraci_optimalni_bez_dolni_meze() -> None:
    result = _solve(project_1d([(1000, 6)], [(6000, None)]))

    assert result.status is SolutionStatus.BEST_FOUND
    assert result.lower_bound is None
