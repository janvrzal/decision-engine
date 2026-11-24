"""Formát čísel `cs-CZ` pro texty generované backendem (SVG, PDF), viz obsah.md."""

from decimal import Decimal

NBSP = "\u00a0"


def number(value: int | Decimal) -> str:
    """Číslo s nezlomitelnou mezerou jako oddělovačem tisíců a desetinnou čárkou: `4 003,5`.

    Celé hodnoty (i `Decimal("3.0")`) jsou bez desetinné části.
    """
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    if isinstance(magnitude, Decimal) and magnitude != magnitude.to_integral_value():
        whole, fraction = f"{magnitude:,.1f}".split(".")
        return sign + whole.replace(",", NBSP) + "," + fraction
    return sign + f"{int(magnitude):,}".replace(",", NBSP)


def millimeters(value: int | Decimal) -> str:
    """Délka s jednotkou: `6 000 mm`."""
    return f"{number(value)}{NBSP}mm"


def bars_word(count: int) -> str:
    """Česky skloňované „tyč“: 1 tyč, 2–4 tyče, 5+ tyčí."""
    if count == 1:
        return "tyč"
    if 2 <= count <= 4:
        return "tyče"
    return "tyčí"
