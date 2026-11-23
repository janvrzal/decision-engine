"""Barvy plánu v backendu se shodují s tokeny design systému (plan-rezani.md)."""

import re
from pathlib import Path

import pytest

from decision_engine.core.render.plan_colors import PLAN_COLORS, PLAN_PART_COLORS

TOKENS = Path(__file__).resolve().parents[3] / "docs" / "design-system" / "tokens.css"


def _tokens() -> dict[str, str]:
    text = TOKENS.read_text(encoding="utf-8")
    return {
        name: value.lower()
        for name, value in re.findall(r"--color-([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", text)
    }


def test_barvy_typu_dilu() -> None:
    tokens = _tokens()
    expected = tuple(tokens[f"plan-part-{index}"] for index in range(1, 9))

    assert expected == PLAN_PART_COLORS


@pytest.mark.parametrize("name", sorted(PLAN_COLORS))
def test_ostatni_barvy(name: str) -> None:
    assert _tokens()[name] == PLAN_COLORS[name]
