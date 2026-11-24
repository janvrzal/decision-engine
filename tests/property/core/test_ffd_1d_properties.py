"""Property testy FFD 1D: validátor nenajde porušení na náhodných zakázkách."""

from decimal import Decimal
from random import Random

from hypothesis import given, settings
from hypothesis import strategies as st

from decision_engine.core.model.calculation import SolutionStatus
from decision_engine.core.model.cutting_1d import (
    Objective,
    Parameters,
    Part,
    Problem,
    Project,
    StockLength,
)
from decision_engine.core.solvers.cutting_1d.bounds import objective_value
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.validation.check_cutting_1d import check_cutting_1d


@st.composite
def projects(draw: st.DrawFn) -> Project:
    stock_lengths = draw(st.lists(st.integers(500, 12_000), min_size=1, max_size=3, unique=True))
    # Prořez i ořez smějí mít desetiny mm (ADR-0011).
    trim = Decimal(draw(st.integers(0, min(500, (min(stock_lengths) - 1) * 10)))) / 10
    parts = tuple(
        Part(
            id=f"p{i}",
            name=f"díl {i}",
            length_mm=draw(st.integers(1, 13_000)),
            quantity=draw(st.integers(1, 12)),
        )
        for i in range(draw(st.integers(1, 6)))
    )
    stock = tuple(
        StockLength(id=f"s{i}", length_mm=length, price=Decimal(draw(st.integers(1, 2000))))
        for i, length in enumerate(stock_lengths)
    )
    return Project(
        id="z",
        name="Náhodná zakázka",
        format_version=1,
        task_type="cutting_1d",
        revision=0,
        problem=Problem(material=None, parts=parts, stock=stock),
        parameters=Parameters(
            kerf_mm=Decimal(draw(st.integers(0, 60))) / 10,
            trim_mm=trim,
            min_remnant_mm=draw(st.integers(0, 1000)),
            objective=draw(st.sampled_from(Objective)),
        ),
    )


@settings(max_examples=200, deadline=None)
@given(projects())
def test_vysledek_projde_validatorem(project: Project) -> None:
    result = solve_ffd(project)

    assert check_cutting_1d(project, result) == ()
    if result.status is SolutionStatus.OPTIMAL:
        # „Optimální“ jen při dosažení dolní meze (pravidlo 9).
        assert result.lower_bound is not None
        assert objective_value(project, result.bars) == result.lower_bound


@settings(max_examples=200, deadline=None)
@given(projects())
def test_pocet_tyci_neni_pod_dolni_mezi(project: Project) -> None:
    result = solve_ffd(project)
    params = project.parameters
    # Kapacita tyče v jednotkách (délka + prořez) je L + prořez - ořez; nejdelší tyč je horní.
    capacity = max(s.length_mm for s in project.problem.stock) + params.kerf_mm - params.trim_mm
    demand = sum(p.length_mm + params.kerf_mm for bar in result.bars for p in bar.pieces)

    assert result.metrics.bars_used * capacity >= demand


@settings(max_examples=100, deadline=None)
@given(projects(), st.randoms(use_true_random=False))
def test_poradi_dilu_v_zadani_nemeni_spotrebu(project: Project, rnd: Random) -> None:
    parts = list(project.problem.parts)
    rnd.shuffle(parts)
    # Díly stejné délky se mohou prohodit, spotřeba a metriky se nemění.
    if len({p.length_mm for p in parts}) != len(parts):
        return
    shuffled = project.model_copy(
        update={"problem": project.problem.model_copy(update={"parts": tuple(parts)})}
    )

    assert solve_ffd(shuffled).metrics == solve_ffd(project).metrics


def _brute_force_optimum(project: Project) -> Decimal | None:
    """Nejlepší hodnota cíle úplným prohledáním rozdělení kusů do tyčí (jen malé zakázky)."""
    params = project.parameters
    pieces = [p.length_mm for p in project.problem.parts for _ in range(p.quantity)]

    def bar_cost(group: list[int]) -> Decimal | None:
        need = sum(Decimal(x) + params.kerf_mm for x in group)
        costs = [
            Decimal(1)
            if params.objective is Objective.FEWEST_BARS
            else Decimal(s.length_mm)
            if params.objective is Objective.LEAST_MATERIAL
            else s.price
            for s in project.problem.stock
            if need <= Decimal(s.length_mm) - params.trim_mm + params.kerf_mm
        ]
        usable = [c for c in costs if c is not None]
        return min(usable) if usable else None

    best: Decimal | None = None

    def partitions(items: list[int]) -> list[list[list[int]]]:
        if not items:
            return [[]]
        first, rest = items[0], items[1:]
        found: list[list[list[int]]] = []
        for part in partitions(rest):
            found.append([[first], *part])
            for i in range(len(part)):
                found.append([*part[:i], [first, *part[i]], *part[i + 1 :]])
        return found

    for partition in partitions(pieces):
        costs = [bar_cost(group) for group in partition]
        if any(cost is None for cost in costs):
            continue
        total = sum((c or Decimal(0) for c in costs), Decimal(0))
        best = total if best is None else min(best, total)
    return best


@st.composite
def small_projects(draw: st.DrawFn) -> Project:
    stock_lengths = draw(st.lists(st.integers(1_000, 4_000), min_size=1, max_size=2, unique=True))
    parts = tuple(
        Part(
            id=f"p{i}",
            name=f"díl {i}",
            length_mm=draw(st.integers(200, 1_000)),
            quantity=draw(st.integers(1, 2)),
        )
        for i in range(draw(st.integers(1, 3)))
    )
    stock = tuple(
        StockLength(id=f"s{i}", length_mm=length, price=Decimal(draw(st.integers(1, 500))))
        for i, length in enumerate(stock_lengths)
    )
    return Project(
        id="z",
        name="Malá zakázka",
        format_version=1,
        task_type="cutting_1d",
        revision=0,
        problem=Problem(material=None, parts=parts, stock=stock),
        parameters=Parameters(
            kerf_mm=Decimal(draw(st.integers(0, 40))) / 10,
            trim_mm=Decimal(draw(st.integers(0, 50))),
            min_remnant_mm=0,
            objective=draw(st.sampled_from(Objective)),
        ),
    )


@settings(max_examples=200, deadline=None)
@given(small_projects())
def test_dolni_mez_a_optimum_odpovidaji_uplnemu_prohledani(project: Project) -> None:
    result = solve_ffd(project)
    optimum = _brute_force_optimum(project)
    value = objective_value(project, result.bars)

    assert optimum is not None
    assert value is not None
    assert result.lower_bound is not None
    assert result.lower_bound <= optimum <= value
    if result.status is SolutionStatus.OPTIMAL:
        assert value == optimum
