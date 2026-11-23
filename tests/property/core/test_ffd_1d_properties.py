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
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.validation.check_cutting_1d import check_cutting_1d


@st.composite
def projects(draw: st.DrawFn) -> Project:
    stock_lengths = draw(st.lists(st.integers(500, 12_000), min_size=1, max_size=3, unique=True))
    trim = draw(st.integers(0, min(50, min(stock_lengths) - 1)))
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
            kerf_mm=draw(st.integers(0, 6)),
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
    assert result.status is not SolutionStatus.OPTIMAL


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
