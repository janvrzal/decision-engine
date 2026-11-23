"""Výsledek jako hodnota: `Ok` nebo `Err` místo výjimek (ADR-0001).

Funkce jádra a portů vracejí `Result[T, E]` a volající ho rozliší přes `match`:

    match parse_project(data):
        case Ok(project): ...
        case Err(errors): ...
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Úspěšný výsledek s hodnotou."""

    value: T


@dataclass(frozen=True, slots=True)
class Err[E]:
    """Neúspěšný výsledek s popisem chyby."""

    error: E


type Result[T, E] = Ok[T] | Err[E]
