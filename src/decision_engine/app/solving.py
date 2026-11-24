"""Výpočet plánu přes registr schopností (port `Solver`).

Každý výsledek projde nezávislým validátorem schopnosti. Porušení je chyba programu,
ne stav, který by se smělo ukázat uživateli jako plán (skill `overeni-solveru`).
"""

import time

from decision_engine.capabilities.registry import find_capability
from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Project


class SolverInvariantError(RuntimeError):
    """Solver vrátil plán, který neprošel validátorem."""


class RegistrySolver:
    """`Solver`, který podle typu úlohy zavolá schopnost z registru a ověří výsledek."""

    def solve(self, project: Project) -> CalculationResult:
        capability = find_capability(project.task_type)
        if capability is None:  # pragma: no cover - typ úlohy hlídá validace zakázky
            raise SolverInvariantError(f"Schopnost {project.task_type} není implementovaná.")
        deadline = time.monotonic() + project.parameters.time_limit_s
        result = capability.solve(project, lambda: time.monotonic() > deadline)
        violations = capability.check(project, result)
        if violations:
            details = "; ".join(f"{v.code}: {v.message}" for v in violations)
            raise SolverInvariantError(f"Plán neprošel validátorem: {details}")
        return result
