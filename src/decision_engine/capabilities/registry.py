"""Statický registr schopností (spec kap. 7 Schopnosti a služby, skill `nova-schopnost`).

Schopnost spojuje identifikátor, název pro UI, výpočet a nezávislý validátor výsledku.
Router a UI smějí nabízet jen schopnosti z tohoto seznamu (AGENTS.md pravidlo 9).
"""

from collections.abc import Callable
from dataclasses import dataclass

from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.validation.check_cutting_1d import Violation, check_cutting_1d


@dataclass(frozen=True, slots=True)
class Capability:
    id: str
    label: str
    """Název v jazyce dílny pro UI."""
    solve: Callable[[Project], CalculationResult]
    check: Callable[[Project, CalculationResult], tuple[Violation, ...]]


CUTTING_1D = Capability(
    id="cutting_1d",
    label="Řezání tyčí",
    solve=solve_ffd,
    check=check_cutting_1d,
)

CAPABILITIES: tuple[Capability, ...] = (CUTTING_1D,)


def find_capability(capability_id: str) -> Capability | None:
    """Schopnost podle identifikátoru, nebo `None`, pokud není implementovaná."""
    return next((c for c in CAPABILITIES if c.id == capability_id), None)
