"""Metriky plánu 1D (spec kap. 4 Výsledek): spotřeba, zbytky, odpad, výtěžnost."""

from decision_engine.core.model.calculation import Bar, Metrics
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.solvers.cutting_1d.geometry import remainder


def compute_metrics(project: Project, bars: tuple[Bar, ...]) -> Metrics:
    """Spočítá metriky z umístěných kusů."""
    parameters = project.parameters
    parts_length = sum(piece.length_mm for bar in bars for piece in bar.pieces)
    consumed = sum(bar.length_mm for bar in bars)
    remnants = [
        length
        for kind, length in (remainder(bar.length_mm, bar.pieces, parameters) for bar in bars)
        if kind == "remnant"
    ]
    remnant_length = sum(remnants)
    by_stock = tuple(
        (stock.id, sum(1 for bar in bars if bar.stock_id == stock.id))
        for stock in project.problem.stock
    )
    return Metrics(
        bars_used=len(bars),
        bars_by_stock=tuple(item for item in by_stock if item[1] > 0),
        parts_length_mm=parts_length,
        consumed_length_mm=consumed,
        remnant_length_mm=remnant_length,
        remnant_count=len(remnants),
        waste_length_mm=consumed - parts_length - remnant_length,
        yield_ratio=parts_length / consumed if consumed else 0.0,
    )
