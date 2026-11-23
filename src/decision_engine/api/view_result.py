"""View model výsledku (Panel Plán): štítek, neaktuálnost, SVG, metriky, rozpis."""

from collections import Counter

from decision_engine.api.view_model import (
    BarsByLength,
    BarView,
    MetricsView,
    PieceView,
    ResultView,
    UnplacedView,
)
from decision_engine.core.model.calculation import Bar, CalculationResult, SolutionStatus
from decision_engine.core.model.cutting_1d import Parameters
from decision_engine.core.render.groups import group_bars
from decision_engine.core.render.svg_1d import render_svg
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
        status=result.status,
        status_label=STATUS_LABEL[result.status],
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
        cuts_mm=tuple(
            p.start_mm + p.length_mm for p in bar.pieces if p.start_mm + p.length_mm < bar.length_mm
        ),
        tail=kind,
        tail_length_mm=tail,
    )
