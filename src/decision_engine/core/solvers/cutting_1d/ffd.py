"""First Fit Decreasing pro více skladových délek (spec kap. 7, 1D solver krok 1).

Kusy se seřadí sestupně a každý jde do první otevřené tyče, kam se vejde. Když se
nevejde nikam, otevře se nová tyč; skladová délka se vybere podle poměru zvoleného cíle
na zabalenou délku dílů (zkusmé naplnění zbývajícími kusy). Výsledek je vždy platné
řešení a horní mez pro pozdější optimalizaci; „Optimální“ neprokazuje.
"""

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

from decision_engine.core.model.calculation import (
    Bar,
    CalculationResult,
    PlacedPiece,
    SolutionStatus,
    UnplacedPiece,
)
from decision_engine.core.model.cutting_1d import Objective, Parameters, Project, StockLength
from decision_engine.core.solvers.cutting_1d.geometry import fits, next_start
from decision_engine.core.solvers.cutting_1d.metrics import compute_metrics


@dataclass(frozen=True, slots=True)
class _Piece:
    part_id: str
    length_mm: int
    order: int
    """Pořadí dílu v zakázce, aby řazení bylo deterministické."""


@dataclass(slots=True)
class _OpenBar:
    stock: StockLength
    pieces: list[PlacedPiece] = field(default_factory=lambda: [])

    def try_add(self, piece: _Piece, parameters: Parameters) -> bool:
        if not fits(self.stock.length_mm, self.pieces, piece.length_mm, parameters):
            return False
        start = next_start(self.pieces, parameters)
        placed = PlacedPiece(part_id=piece.part_id, length_mm=piece.length_mm, start_mm=start)
        self.pieces.append(placed)
        return True


def solve_ffd(project: Project) -> CalculationResult:
    """Spočítá plán řezání heuristikou FFD."""
    parameters = project.parameters
    pieces = _sorted_pieces(project)
    longest = max(stock.length_mm for stock in project.problem.stock)
    placeable = [p for p in pieces if fits(longest, [], p.length_mm, parameters)]
    too_long = Counter(p.part_id for p in pieces if not fits(longest, [], p.length_mm, parameters))

    open_bars: list[_OpenBar] = []
    for index, piece in enumerate(placeable):
        if any(bar.try_add(piece, parameters) for bar in open_bars):
            continue
        stock = _choose_stock(project, placeable[index:])
        bar = _OpenBar(stock)
        bar.try_add(piece, parameters)
        open_bars.append(bar)

    bars = tuple(
        Bar(stock_id=bar.stock.id, length_mm=bar.stock.length_mm, pieces=tuple(bar.pieces))
        for bar in open_bars
    )
    unplaced = tuple(
        UnplacedPiece(part_id=part.id, quantity=too_long[part.id], reason="too_long")
        for part in project.problem.parts
        if too_long[part.id]
    )
    return CalculationResult(
        status=_status(bars, unplaced),
        source=project,
        bars=bars,
        unplaced=unplaced,
        metrics=compute_metrics(project, bars),
    )


def _sorted_pieces(project: Project) -> list[_Piece]:
    pieces = [
        _Piece(part_id=part.id, length_mm=part.length_mm, order=order)
        for order, part in enumerate(project.problem.parts)
        for _ in range(part.quantity)
    ]
    return sorted(pieces, key=lambda p: (-p.length_mm, p.order))


def _choose_stock(project: Project, remaining: list[_Piece]) -> StockLength:
    """Skladová délka s nejlepším poměrem cíle na zabalenou délku pro zbývající kusy."""
    parameters = project.parameters
    first = remaining[0]
    best: tuple[Decimal, int, StockLength] | None = None
    for index, stock in enumerate(project.problem.stock):
        if not fits(stock.length_mm, [], first.length_mm, parameters):
            continue
        packed = _trial_fill(stock, remaining, parameters)
        ratio = _objective_cost(stock, parameters.objective) / Decimal(packed)
        if best is None or (ratio, index) < (best[0], best[1]):
            best = (ratio, index, stock)
    assert best is not None  # kus je umístitelný, takže se vejde aspoň do nejdelší tyče
    return best[2]


def _trial_fill(stock: StockLength, remaining: list[_Piece], parameters: Parameters) -> int:
    """Délka dílů, které by FFD dalo do jedné nové tyče této délky (první kus vždy)."""
    trial = _OpenBar(stock)
    for piece in remaining:
        trial.try_add(piece, parameters)
    return sum(piece.length_mm for piece in trial.pieces)


def _objective_cost(stock: StockLength, objective: Objective) -> Decimal:
    match objective:
        case Objective.CHEAPEST:
            # Validace zakázky zaručuje cenu u všech délek při tomto cíli.
            return stock.price if stock.price is not None else Decimal(stock.length_mm)
        case Objective.LEAST_MATERIAL:
            return Decimal(stock.length_mm)
        case Objective.FEWEST_BARS:
            return Decimal(1)


def _status(bars: tuple[Bar, ...], unplaced: tuple[UnplacedPiece, ...]) -> SolutionStatus:
    if not bars and unplaced:
        return SolutionStatus.INFEASIBLE
    if unplaced:
        return SolutionStatus.PARTIAL
    return SolutionStatus.BEST_FOUND
