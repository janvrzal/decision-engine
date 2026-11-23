"""RegistrySolver: skutečný plán projde, plán porušující invarianty se nesmí vrátit."""

import pytest
from solver_cases import project_1d

from decision_engine.app import solving
from decision_engine.app.solving import RegistrySolver, SolverInvariantError
from decision_engine.capabilities.registry import CUTTING_1D, Capability
from decision_engine.core.model.calculation import CalculationResult, SolutionStatus
from decision_engine.core.model.cutting_1d import Project

PROJECT = project_1d([(2000, 3)], [(6000, None)], kerf=3)


def test_plan_z_registru_projde_validatorem() -> None:
    result = RegistrySolver().solve(PROJECT)

    assert result.status is SolutionStatus.BEST_FOUND
    assert result.metrics.bars_used == 2


def test_neplatny_plan_je_chyba_programu(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(project: Project) -> CalculationResult:
        return CUTTING_1D.solve(project).model_copy(update={"status": SolutionStatus.OPTIMAL})

    capability = Capability(id="cutting_1d", label="test", solve=broken, check=CUTTING_1D.check)

    def find(capability_id: str) -> Capability:
        return capability

    monkeypatch.setattr(solving, "find_capability", find)

    with pytest.raises(SolverInvariantError, match="label"):
        RegistrySolver().solve(PROJECT)
