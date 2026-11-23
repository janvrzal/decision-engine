"""Barvy plánu řezání: kopie tokenů z `docs/design-system/tokens.css` (plan-rezani.md).

SVG generuje backend, proto potřebuje hodnoty tokenů jako konstanty. Test
`test_plan_colors.py` hlídá, že se s `tokens.css` shodují.
"""

PLAN_PART_COLORS: tuple[str, ...] = (
    "#9fc4e8",
    "#a3d6c4",
    "#c6dc9e",
    "#d7bce4",
    "#f0bba6",
    "#b9c4da",
    "#e7c6d2",
    "#bfe0e8",
)
"""`--color-plan-part-1` až `-8`; od 9. typu dílu se opakují."""

PLAN_COLORS: dict[str, str] = {
    "plan-bar": "#efede8",
    "plan-remnant": "#dcefe1",
    "plan-waste": "#f1efea",
    "plan-waste-hatch": "#7d776c",
    "plan-kerf": "#1d1b18",
    "plan-cut": "#a14f06",
    "plan-highlight": "#a14f06",
    "surface": "#ffffff",
    "border-strong": "#8c8679",
    "ink": "#1d1b18",
    "ink-muted": "#5c574e",
    "success": "#0b6b5f",
}
"""Ostatní tokeny použité v SVG, klíč = název tokenu bez `--color-`."""


def part_color(type_index: int) -> str:
    """Barva typu dílu podle jeho pořadí v zakázce (od 0)."""
    return PLAN_PART_COLORS[type_index % len(PLAN_PART_COLORS)]
