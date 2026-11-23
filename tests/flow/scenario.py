"""Pomůcky pro testy toku: posloupnost událostí přes reducer bez adaptérů."""

from collections.abc import Iterable
from decimal import Decimal

from decision_engine.core.effects import Effect, RunSolver
from decision_engine.core.events import Event, SolveFinished
from decision_engine.core.model.calculation import CalculationResult, SolutionStatus
from decision_engine.core.model.cutting_1d import Objective
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)
from decision_engine.core.reducer import reduce
from decision_engine.core.state import AppState, initial_state


def run(
    events: Iterable[Event], state: AppState | None = None
) -> tuple[AppState, tuple[Effect, ...]]:
    """Projde události reducerem; vrátí konečný stav a efekty z poslední události."""
    current = state if state is not None else initial_state("relace-1")
    effects: tuple[Effect, ...] = ()
    for event in events:
        current, effects = reduce(current, event)
    return current, effects


def shelf_proposal(
    base_revision: int | None = None,
    *,
    shelf_length: int | None = 1200,
    price: Decimal | None = Decimal("320.00"),
    objective: Objective = Objective.CHEAPEST,
) -> ChangeProposal:
    """Návrh zakázky regálu, jak by ho vrátila extrakce."""
    return ChangeProposal(
        base_revision=base_revision,
        name="Regál do dílny",
        material="jekl 40×40×2",
        parts=(
            PartDraft(id="p1", name="noha", length_mm=1800, quantity=4),
            PartDraft(id="p2", name="polička", length_mm=shelf_length, quantity=8),
        ),
        stock=(StockLengthDraft(id="s1", length_mm=6000, price=price),),
        parameters=ParametersDraft(kerf_mm=3, trim_mm=0, min_remnant_mm=300, objective=objective),
        unconfirmed=frozenset({("parameters", "kerf_mm")}),
    )


def solved(effects: tuple[Effect, ...]) -> SolveFinished:
    """Výsledek solveru pro jediný `RunSolver` v efektech."""
    match effects:
        case (RunSolver(project=project),):
            return SolveFinished(
                result=CalculationResult(status=SolutionStatus.OPTIMAL, source=project)
            )
        case _:
            raise AssertionError(f"čekal jsem jeden RunSolver, přišlo {effects}")
