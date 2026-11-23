"""Výsledek výpočtu. Plán, metriky a dolní mez doplní solver (#12)."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.cutting_1d import Project


class SolutionStatus(StrEnum):
    """Stav plánu (spec kap. 4): štítek se „Optimální“ jen při prokázaném optimu."""

    OPTIMAL = "optimal"
    BEST_FOUND = "best_found"
    PARTIAL = "partial"
    INFEASIBLE = "infeasible"


class CalculationResult(BaseModel):
    """Výsledek výpočtu nesoucí revizi zakázky, ze které vznikl."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: SolutionStatus
    source: Project
    """Potvrzená revize zakázky, ze které výsledek vznikl (pro odvození neaktuálnosti)."""
