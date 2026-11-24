"""Validátor plánu 1D musí odhalit ručně pokažené výsledky."""

from decimal import Decimal
from typing import Any

from solver_cases import project_1d

from decision_engine.core.model.calculation import (
    Bar,
    CalculationResult,
    PlacedPiece,
    SolutionStatus,
    UnplacedPiece,
)
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.validation.check_cutting_1d import check_cutting_1d

PROJECT = project_1d([(2000, 2), (1000, 1)], [(6000, None)], kerf=3)
VALID = solve_ffd(PROJECT)


def _codes(result: CalculationResult) -> set[str]:
    return {violation.code for violation in check_cutting_1d(PROJECT, result)}


def _with_bar(bar: Bar, **changes: Any) -> CalculationResult:
    return VALID.model_copy(update={"bars": (bar.model_copy(update=changes),)})


def test_platny_plan_projde() -> None:
    assert check_cutting_1d(PROJECT, VALID) == ()


def test_chybejici_kus() -> None:
    bar = VALID.bars[0]
    assert "count" in _codes(_with_bar(bar, pieces=bar.pieces[:-1]))


def test_kusy_se_prekryvaji_kvuli_prorezu() -> None:
    pieces = (
        PlacedPiece(part_id="p1", length_mm=2000, start_mm=Decimal(0)),
        PlacedPiece(part_id="p1", length_mm=2000, start_mm=Decimal(2001)),
        PlacedPiece(part_id="p2", length_mm=1000, start_mm=Decimal(4004)),
    )
    assert "overlap" in _codes(_with_bar(VALID.bars[0], pieces=pieces))


def test_prekrocena_kapacita() -> None:
    pieces = (
        PlacedPiece(part_id="p1", length_mm=2000, start_mm=Decimal(0)),
        PlacedPiece(part_id="p1", length_mm=2000, start_mm=Decimal(2003)),
        PlacedPiece(part_id="p2", length_mm=1000, start_mm=Decimal(5006)),
    )
    assert "capacity" in _codes(_with_bar(VALID.bars[0], pieces=pieces))


def test_kus_s_jinou_delkou_nez_dil() -> None:
    bar = VALID.bars[0]
    wrong = bar.pieces[0].model_copy(update={"length_mm": 1999})
    assert "wrong_piece" in _codes(_with_bar(bar, pieces=(wrong, *bar.pieces[1:])))


def test_neznama_skladova_delka() -> None:
    assert "unknown_stock" in _codes(_with_bar(VALID.bars[0], length_mm=5000))


def test_spatne_metriky() -> None:
    metrics = VALID.metrics.model_copy(update={"waste_length_mm": 0, "yield_ratio": 0.5})
    assert "metrics" in _codes(VALID.model_copy(update={"metrics": metrics}))


def test_zbytecne_neumisteny_kus() -> None:
    bar = VALID.bars[0]
    result = _with_bar(bar, pieces=bar.pieces[:-1]).model_copy(
        update={
            "unplaced": (UnplacedPiece(part_id="p2", quantity=1, reason="too_long"),),
            "status": SolutionStatus.PARTIAL,
        }
    )
    codes = _codes(result)
    assert "needlessly_unplaced" in codes


def test_optimalni_bez_dolni_meze() -> None:
    assert "label" in _codes(VALID.model_copy(update={"status": SolutionStatus.OPTIMAL}))


def test_castecny_bez_neumistenych_kusu() -> None:
    assert "label" in _codes(VALID.model_copy(update={"status": SolutionStatus.PARTIAL}))


def test_vysledek_jine_revize() -> None:
    other = PROJECT.model_copy(update={"revision": 5})
    assert "wrong_source" in _codes(VALID.model_copy(update={"source": other}))
