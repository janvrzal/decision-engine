"""View model výsledku (Panel Plán): štítek, neaktuálnost, SVG, metriky, rozpis."""

from collections import Counter
from decimal import Decimal

from decision_engine.api.view_model import (
    BarsByLength,
    BarView,
    CostLineView,
    CostView,
    MetricsView,
    PieceView,
    ResultView,
    UnplacedView,
)
from decision_engine.core.costing import material_cost
from decision_engine.core.model.calculation import Bar, CalculationResult, SolutionStatus
from decision_engine.core.model.cutting_1d import Objective, Parameters
from decision_engine.core.render.format import NBSP, bars_word, millimeters, number
from decision_engine.core.render.groups import group_bars
from decision_engine.core.render.svg_1d import render_svg
from decision_engine.core.solvers.cutting_1d.bounds import objective_value
from decision_engine.core.solvers.cutting_1d.geometry import remainder

STATUS_LABEL = {
    SolutionStatus.OPTIMAL: "Optimální",
    SolutionStatus.BEST_FOUND: "Nejlepší nalezený",
    SolutionStatus.PARTIAL: "Částečný",
    SolutionStatus.INFEASIBLE: "Bez řešení",
}
UNPLACED_REASON = {"too_long": "Díl je delší než nejdelší skladová tyč."}


def build_result(result: CalculationResult, *, stale: bool, proposal_pending: bool) -> ResultView:
    project = result.source
    names = {part.id: part.name for part in project.problem.parts}
    lengths = {part.id: part.length_mm for part in project.problem.parts}
    metrics = result.metrics
    by_length = Counter(bar.length_mm for bar in result.bars)
    return ResultView(
        project_name=project.name,
        material=project.problem.material,
        status=result.status,
        status_label=STATUS_LABEL[result.status],
        status_note=_status_note(result),
        stale=stale,
        stale_reason=(
            None
            if not stale
            else "čekají nepotvrzené změny"
            if proposal_pending
            else "změnily se vstupy plánu"
        ),
        svg=render_svg(result),
        metrics=MetricsView(
            bars_used=metrics.bars_used,
            bars_by_length=tuple(
                BarsByLength(length_mm=length, count=count)
                for length, count in sorted(by_length.items(), key=lambda item: -item[0])
            ),
            parts_length_mm=metrics.parts_length_mm,
            consumed_length_mm=metrics.consumed_length_mm,
            remnant_length_mm=metrics.remnant_length_mm,
            remnant_count=metrics.remnant_count,
            waste_length_mm=metrics.waste_length_mm,
            yield_ratio=metrics.yield_ratio,
        ),
        cost=_cost(result),
        bars=tuple(
            _bar(group.bar, group.numbers, names, project.parameters)
            for group in group_bars(result)
        ),
        unplaced=tuple(
            UnplacedView(
                part_id=item.part_id,
                name=names.get(item.part_id, item.part_id),
                length_mm=lengths.get(item.part_id, 0),
                quantity=item.quantity,
                reason=UNPLACED_REASON[item.reason],
            )
            for item in result.unplaced
        ),
    )


def _status_note(result: CalculationResult) -> str | None:
    """Vysvětlení štítku: u „Nejlepší nalezený“ rozdíl od dolní meze v jednotce cíle."""
    bound = result.lower_bound
    if result.status is SolutionStatus.OPTIMAL:
        return "Plán dosahuje dolní meze pro zvolený cíl; lepší plán neexistuje."
    if result.status is not SolutionStatus.BEST_FOUND or bound is None:
        return None
    value = objective_value(result.source, result.bars)
    if value is None:
        return None
    match result.source.parameters.objective:
        case Objective.FEWEST_BARS:
            gap = f"{number(value - bound)} {bars_word(int(value - bound))}"
            limit = f"{number(bound)} {bars_word(int(bound))}"
        case Objective.LEAST_MATERIAL:
            gap, limit = millimeters(value - bound), millimeters(bound)
        case Objective.CHEAPEST:
            gap, limit = _money(value - bound), _money(bound)
    return (
        f"Dolní mez je {limit}; plán je nejvýš o {gap} nad ní. Lepší plán může existovat, "
        "ale nemusí."
    )


def _money(value: Decimal) -> str:
    whole, fraction = f"{value:,.2f}".split(".")
    return f"{whole.replace(',', NBSP)},{fraction}{NBSP}Kč"


def _cost(result: CalculationResult) -> CostView:
    cost = material_cost(result)
    return CostView(
        lines=tuple(
            CostLineView(
                stock_id=line.stock_id,
                length_mm=line.length_mm,
                count=line.count,
                unit_price=line.unit_price,
                total=line.total,
            )
            for line in cost.lines
        ),
        total=cost.total,
        note=(
            "Cena nejde sečíst: u spotřebované skladové délky chybí cena. Doplňte ji v kroku "
            "Kontrola údajů."
            if cost.missing_price
            else None
        ),
    )


def _bar(
    bar: Bar, numbers: tuple[int, ...], names: dict[str, str], parameters: Parameters
) -> BarView:
    kind, tail = remainder(bar.length_mm, bar.pieces, parameters)
    return BarView(
        numbers=numbers,
        length_mm=bar.length_mm,
        pieces=tuple(
            PieceView(
                part_id=p.part_id,
                name=names.get(p.part_id, p.part_id),
                length_mm=p.length_mm,
                start_mm=p.start_mm,
            )
            for p in bar.pieces
        ),
        # Zarovnávací ořez je první řez: pila nejdřív zarovná čelo tyče.
        cuts_mm=(
            *((parameters.trim_mm,) if parameters.trim_mm > 0 and bar.pieces else ()),
            *(
                p.start_mm + p.length_mm
                for p in bar.pieces
                if p.start_mm + p.length_mm < bar.length_mm
            ),
        ),
        tail=kind,
        tail_length_mm=tail,
    )
