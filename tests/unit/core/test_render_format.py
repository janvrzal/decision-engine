"""Formát čísel v textech backendu (SVG): tisíce s NBSP, desetinná čárka (obsah.md)."""

from decimal import Decimal

import pytest

from decision_engine.core.render.format import NBSP, millimeters, number


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (4003, f"4{NBSP}003"),
        (Decimal("2005.5"), f"2{NBSP}005,5"),
        (Decimal("3.0"), "3"),
        (Decimal("-1.5"), "-1,5"),
    ],
)
def test_cislo_v_cs_cz(value: int | Decimal, text: str) -> None:
    assert number(value) == text


def test_delka_s_jednotkou() -> None:
    assert millimeters(Decimal("2.5")) == f"2,5{NBSP}mm"
