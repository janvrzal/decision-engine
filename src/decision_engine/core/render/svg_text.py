"""Text a souřadnice v SVG plánu: escapování, zkracování popisků, stabilní čísla."""

from xml.sax.saxutils import escape

CHAR_WIDTH = 0.58
"""Průměrná šířka znaku jako podíl velikosti písma (IBM Plex Sans), pro zkracování."""


def text_width(text: str, size: int) -> float:
    return len(text) * size * CHAR_WIDTH


def fit(text: str, width: float, *, size: int, keep: str = "") -> str:
    """Text zkrácený „…“, aby se vešel do šířky; `keep` (např. délka) zůstane celé.

    Plný název je vždy v `<title>` dílu a v rozpisu po tyčích (textová alternativa).
    """
    if text_width(text, size) <= width:
        return text
    head = text[: len(text) - len(keep)] if keep else text
    room = int(width / (size * CHAR_WIDTH)) - len(keep) - 1
    if room < 2:
        return keep.strip() if keep and text_width(keep.strip(), size) <= width else ""
    return head[:room].rstrip() + "…" + keep


def text(
    x: float,
    y: float,
    content: str,
    size: int,
    fill: str,
    *,
    weight: int = 400,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{n(x)}" y="{n(y)}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{escape(content)}</text>'
    )


def n(value: float) -> str:
    """Souřadnice zaokrouhlená na setiny bez zbytečných nul (stabilní snapshoty)."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text
