"""Vlastnosti převodu zakázky 1D: round-trip přes JSON a žádná výjimka pro libovolný vstup."""

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from decision_engine.core.model.cutting_1d import (
    Objective,
    Parameters,
    Part,
    Problem,
    Project,
    StockLength,
)
from decision_engine.core.result import Err, Ok
from decision_engine.core.validation.cutting_1d import parse_project

_text = st.text(alphabet=st.characters(categories=("L", "N")), min_size=1, max_size=12)
_prices = st.decimals(min_value=0, max_value=100_000, places=2, allow_nan=False)


@st.composite
def projects(draw: st.DrawFn) -> Project:
    """Platné zakázky: jedinečná id, ořez kratší než tyče, ceny podle cíle."""
    objective = draw(st.sampled_from(Objective))
    part_count = draw(st.integers(min_value=1, max_value=6))
    stock_count = draw(st.integers(min_value=1, max_value=3))
    parts = tuple(
        Part(
            id=f"p{i}",
            name=draw(_text),
            length_mm=draw(st.integers(min_value=1, max_value=20_000)),
            quantity=draw(st.integers(min_value=1, max_value=50)),
        )
        for i in range(part_count)
    )
    stock = tuple(
        StockLength(
            id=f"s{i}",
            length_mm=draw(st.integers(min_value=500, max_value=12_000)),
            price=draw(_prices if objective is Objective.CHEAPEST else st.none() | _prices),
        )
        for i in range(stock_count)
    )
    shortest = min(s.length_mm for s in stock)
    return Project(
        id=draw(_text),
        name=draw(_text),
        format_version=1,
        task_type="cutting_1d",
        revision=draw(st.integers(min_value=0, max_value=1_000)),
        problem=Problem(material=draw(st.none() | _text), parts=parts, stock=stock),
        parameters=Parameters(
            kerf_mm=Decimal(draw(st.integers(min_value=0, max_value=100))) / 10,
            trim_mm=Decimal(draw(st.integers(min_value=0, max_value=shortest - 1))),
            min_remnant_mm=draw(st.integers(min_value=0, max_value=2_000)),
            objective=objective,
        ),
    )


@given(projects())
def test_zakazka_prezije_ulozeni_do_json_a_nacteni(project: Project) -> None:
    # UC-06: uložená a znovu načtená zakázka zachová vstupy.
    assert parse_project(project.model_dump(mode="json")) == Ok(project)


@given(projects())
def test_ceny_zustanou_decimal(project: Project) -> None:
    match parse_project(project.model_dump(mode="json")):
        case Ok(loaded):
            assert all(
                s.price is None or isinstance(s.price, Decimal) for s in loaded.problem.stock
            )
        case Err(errors):
            raise AssertionError(errors)


_json = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats() | st.text(max_size=5),
    lambda children: (
        st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=8), children, max_size=4)
    ),
    max_leaves=20,
)


@given(_json)
def test_libovolny_vstup_nevyhodi_vyjimku(data: object) -> None:
    assert isinstance(parse_project(data), Ok | Err)
