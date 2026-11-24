"""Nezávislý validátor plánu 1D (skill `overeni-solveru`, spec kap. 9).

Záměrně nepoužívá kód solveru: geometrii tyče a metriky počítá znovu po svém, aby chyba
v solveru nezůstala skrytá stejnou chybou ve výpočtu metrik. Vrací seznam porušení;
prázdný seznam znamená platný plán.
"""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from decision_engine.core.model.calculation import Bar, CalculationResult, SolutionStatus
from decision_engine.core.model.cutting_1d import Project

YIELD_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class Violation:
    """Porušené pravidlo plánu."""

    code: str
    message: str
    bar_index: int | None = None


def check_cutting_1d(project: Project, result: CalculationResult) -> tuple[Violation, ...]:
    """Ověří plán proti zakázce: kusy, kapacity, prořez, zbytky, metriky a štítek."""
    violations: list[Violation] = []
    if result.source != project:
        violations.append(Violation("wrong_source", "Výsledek nepatří k této revizi zakázky."))
    for index, bar in enumerate(result.bars):
        violations += _check_bar(project, index, bar)
    violations += _check_pieces(project, result)
    violations += _check_metrics(project, result)
    violations += _check_status(result)
    return tuple(violations)


def _check_bar(project: Project, index: int, bar: Bar) -> list[Violation]:
    params = project.parameters
    stock = {item.id: item.length_mm for item in project.problem.stock}
    parts = {part.id: part.length_mm for part in project.problem.parts}
    found: list[Violation] = []

    def add(code: str, message: str) -> None:
        found.append(Violation(code, message, index))

    if stock.get(bar.stock_id) != bar.length_mm:
        add("unknown_stock", "Tyč neodpovídá žádné skladové délce zakázky.")
    if not bar.pieces:
        add("empty_bar", "Tyč bez kusů se nemá spotřebovat.")
    earliest = params.trim_mm
    for piece in bar.pieces:
        if parts.get(piece.part_id) != piece.length_mm:
            add("wrong_piece", f"Kus „{piece.part_id}“ nemá délku svého dílu.")
        if piece.start_mm < earliest:
            add("overlap", "Kus začíná dřív, než dovoluje ořez nebo prořez před ním.")
        earliest = piece.start_mm + piece.length_mm + params.kerf_mm
    if bar.pieces and earliest - params.kerf_mm > bar.length_mm:
        add("capacity", "Kusy se do tyče nevejdou.")
    return found


def _check_pieces(project: Project, result: CalculationResult) -> list[Violation]:
    params = project.parameters
    placed = Counter(piece.part_id for bar in result.bars for piece in bar.pieces)
    unplaced = Counter[str]()
    for item in result.unplaced:
        unplaced[item.part_id] += item.quantity
    found: list[Violation] = []
    for part in project.problem.parts:
        if placed[part.id] + unplaced[part.id] != part.quantity:
            found.append(
                Violation("count", f"Díl „{part.id}“ není v plánu právě {part.quantity}×.")
            )
    known = {part.id for part in project.problem.parts}
    if set(placed) - known or set(unplaced) - known:
        found.append(Violation("unknown_part", "Plán obsahuje díl, který zakázka nemá."))
    longest_usable = max(s.length_mm for s in project.problem.stock) - params.trim_mm
    lengths = {part.id: part.length_mm for part in project.problem.parts}
    for item in result.unplaced:
        if lengths.get(item.part_id, 0) <= longest_usable:
            found.append(
                Violation("needlessly_unplaced", f"Díl „{item.part_id}“ by se do tyče vešel.")
            )
    return found


def _check_metrics(project: Project, result: CalculationResult) -> list[Violation]:
    params = project.parameters
    metrics = result.metrics
    parts = sum(p.length_mm for bar in result.bars for p in bar.pieces)
    consumed = sum(bar.length_mm for bar in result.bars)
    remnants: list[Decimal] = []
    for bar in result.bars:
        if not bar.pieces:
            continue
        tail = bar.length_mm - (bar.pieces[-1].start_mm + bar.pieces[-1].length_mm)
        usable = tail - params.kerf_mm
        if tail > params.kerf_mm and usable >= params.min_remnant_mm:
            remnants.append(usable)
    counts = Counter(bar.stock_id for bar in result.bars)
    expected = {
        "bars_used": len(result.bars),
        "parts_length_mm": parts,
        "consumed_length_mm": consumed,
        "remnant_length_mm": sum(remnants, Decimal(0)),
        "remnant_count": len(remnants),
        "waste_length_mm": consumed - parts - sum(remnants),
    }
    found = [
        Violation("metrics", f"Metrika {name} nesouhlasí s plánem.")
        for name, value in expected.items()
        if getattr(metrics, name) != value
    ]
    if dict(metrics.bars_by_stock) != dict(counts):
        found.append(Violation("metrics", "Počty tyčí podle skladových délek nesouhlasí."))
    expected_yield = parts / consumed if consumed else 0.0
    if abs(metrics.yield_ratio - expected_yield) > YIELD_TOLERANCE:
        found.append(Violation("metrics", "Výtěžnost nesouhlasí s plánem."))
    return found


def _check_status(result: CalculationResult) -> list[Violation]:
    found: list[Violation] = []
    if result.status is SolutionStatus.OPTIMAL and result.lower_bound is None:
        found.append(Violation("label", "„Optimální“ bez prokázané dolní meze (pravidlo 9)."))
    has_unplaced = bool(result.unplaced)
    if has_unplaced != (result.status in {SolutionStatus.PARTIAL, SolutionStatus.INFEASIBLE}):
        found.append(Violation("label", "Štítek neodpovídá neumístěným kusům."))
    if result.status is SolutionStatus.INFEASIBLE and result.bars:
        found.append(Violation("label", "„Bez řešení“, ale plán obsahuje tyče."))
    return found
