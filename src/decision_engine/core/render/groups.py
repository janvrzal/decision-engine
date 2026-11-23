"""Seskupení stejných tyčí plánu (plan-rezani.md): „4×  Tyč 1–4“.

Stejné tyče = stejná skladová délka a stejné kusy na stejných polohách. Skupiny jsou
seřazené od nejčastější, při shodě podle pořadí ve výsledku solveru. Tyče se číslují
v tomto pořadí, aby plán i rozpis po tyčích používaly stejná čísla.
"""

from dataclasses import dataclass

from decision_engine.core.model.calculation import Bar, CalculationResult


@dataclass(frozen=True, slots=True)
class BarGroup:
    bar: Bar
    """Vzorová tyč skupiny (všechny tyče skupiny jsou stejné)."""
    numbers: tuple[int, ...]
    """Čísla tyčí ve skupině (od 1)."""

    @property
    def count(self) -> int:
        return len(self.numbers)

    def label(self) -> str:
        """„Tyč 3“ nebo „Tyč 1–4“."""
        first, last = self.numbers[0], self.numbers[-1]
        return f"Tyč {first}" if first == last else f"Tyč {first}–{last}"


def group_bars(result: CalculationResult) -> tuple[BarGroup, ...]:
    """Skupiny stejných tyčí s čísly tyčí v pořadí zobrazení."""
    order: list[tuple[object, ...]] = []
    members: dict[tuple[object, ...], list[Bar]] = {}
    for bar in result.bars:
        key = (bar.stock_id, bar.length_mm, tuple((p.part_id, p.start_mm) for p in bar.pieces))
        if key not in members:
            order.append(key)
            members[key] = []
        members[key].append(bar)
    ranked = sorted(order, key=lambda key: (-len(members[key]), order.index(key)))

    groups: list[BarGroup] = []
    next_number = 1
    for key in ranked:
        count = len(members[key])
        numbers = tuple(range(next_number, next_number + count))
        groups.append(BarGroup(bar=members[key][0], numbers=numbers))
        next_number += count
    return tuple(groups)
