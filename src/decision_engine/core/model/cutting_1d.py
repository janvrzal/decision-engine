"""Datové objekty zakázky řezání tyčí (spec kap. 5 UC-01, kap. 7 Hlavní datové objekty).

Délky jsou `int` v milimetrech, peníze `Decimal` (ADR-0002). Modely jsou neměnné
a kolekce jsou `tuple` (ADR-0001). Obsahují jen potvrzená data zakázky; výchozí
a odhadnuté hodnoty patří do návrhu změny (`ChangeProposal`), dokud je uživatel nepotvrdí.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_LENGTH_MM = 100_000
"""Nejdelší délka, kterou aplikace přijme (100 m); delší je skoro jistě překlep."""
MAX_QUANTITY = 10_000
"""Nejvyšší počet kusů jednoho dílu."""
MAX_PIECES = 5_000
"""Nejvyšší počet kusů celé zakázky (spec kap. 8): výpočet tak zůstane v řádu sekund."""
MAX_PRICE = Decimal("10000000")
"""Nejvyšší cena jedné tyče v Kč."""
MAX_TIME_LIMIT_S = 120
"""Nejdelší časový limit výpočtu v sekundách."""
MAX_PARTS = 500
MAX_STOCK = 50

type Millimeters = Annotated[int, Field(gt=0, le=MAX_LENGTH_MM)]
"""Kladná délka v celých milimetrech."""

type NonNegativeMillimeters = Annotated[int, Field(ge=0, le=MAX_LENGTH_MM)]
"""Nezáporná délka v celých milimetrech (prořez, ořez, minimální zbytek)."""

type Money = Annotated[Decimal, Field(ge=0, le=MAX_PRICE, decimal_places=2)]
"""Nezáporná částka v Kč s nejvýš dvěma desetinnými místy."""

MAX_TEXT_CHARS = 200
"""Nejdelší název zakázky, dílu nebo materiálu (vejde se do názvu souboru i plánu)."""

type Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_TEXT_CHARS)
]
"""Neprázdný text bez okrajových mezer."""


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Objective(StrEnum):
    """Cíl optimalizace, který si uživatel zvolí (spec UC-01)."""

    CHEAPEST = "cheapest"
    """Nejnižší cena materiálu: součet cen spotřebovaných tyčí."""
    FEWEST_BARS = "fewest_bars"
    """Nejméně tyčí: počet spotřebovaných tyčí."""
    LEAST_MATERIAL = "least_material"
    """Nejméně materiálu: součet délek spotřebovaných tyčí."""


class Part(_Frozen):
    """Požadovaný díl: kolik kusů jaké délky."""

    id: Text
    """Stabilní identita dílu v zakázce (návrhy změn a solver na ni odkazují)."""
    name: Text
    length_mm: Millimeters
    quantity: Annotated[int, Field(gt=0, le=MAX_QUANTITY)]


class StockLength(_Frozen):
    """Skladová délka tyče, ze které se řeže, a její cena za kus."""

    id: Text
    length_mm: Millimeters
    price: Money | None
    """Cena za kus v Kč; `None` znamená, že cena chybí (nikdy ne 0 Kč)."""


class Problem(_Frozen):
    """Zadání úlohy: materiál, požadované díly a dostupné skladové délky."""

    material: Text | None
    parts: Annotated[tuple[Part, ...], Field(min_length=1, max_length=MAX_PARTS)]
    stock: Annotated[tuple[StockLength, ...], Field(min_length=1, max_length=MAX_STOCK)]


class Parameters(_Frozen):
    """Parametry výpočtu (spec kap. 7)."""

    kerf_mm: NonNegativeMillimeters
    """Prořez: šířka materiálu, kterou odebere jeden řez."""
    trim_mm: NonNegativeMillimeters
    """Zarovnávací ořez začátku tyče; odečte se od její délky."""
    min_remnant_mm: NonNegativeMillimeters
    """Minimální délka využitelného zbytku; kratší zbytek je odpad."""
    objective: Objective
    time_limit_s: Annotated[int, Field(gt=0, le=MAX_TIME_LIMIT_S)] = 10
    """Časový limit výpočtu v sekundách."""


class Project(_Frozen):
    """Potvrzená revize zakázky řezání tyčí."""

    id: Text
    name: Text
    format_version: Literal[1]
    task_type: Literal["cutting_1d"]
    revision: Annotated[int, Field(ge=0)]
    problem: Problem
    parameters: Parameters
