"""Formát čísel `cs-CZ` pro texty generované backendem (SVG, PDF), viz obsah.md."""

NBSP = "\u00a0"


def number(value: int) -> str:
    """Celé číslo s nezlomitelnou mezerou jako oddělovačem tisíců: `4 003`."""
    sign = "-" if value < 0 else ""
    return sign + f"{abs(value):,}".replace(",", NBSP)


def millimeters(value: int) -> str:
    """Délka s jednotkou: `6 000 mm`."""
    return f"{number(value)}{NBSP}mm"


def bars_word(count: int) -> str:
    """Česky skloňované „tyč“: 1 tyč, 2–4 tyče, 5+ tyčí."""
    if count == 1:
        return "tyč"
    if 2 <= count <= 4:
        return "tyče"
    return "tyčí"
