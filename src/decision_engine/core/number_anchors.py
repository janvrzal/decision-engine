"""Ukotvení čísel z výstupu modelu (AGENTS.md pravidlo 8, Issue #54).

Číslo, které model vrátí, musí mít oporu ve vstupu: ve zprávě uživatele (po převodu
mm/cm/m) nebo v potvrzené zakázce. Co oporu nemá, je odhad AI a označí se jako
nepotvrzené, i když ho model sám za nejisté neoznačil. Nespoléháme tak jen na to,
co model o sobě přizná.
"""

import re
from decimal import Decimal, InvalidOperation
from itertools import pairwise

from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.model.proposal import ChangeProposal

_NUMBER = re.compile(r"\d+(?:\s\d{3})*(?:[.,]\d+)?")

_WORDS = {
    "jeden": 1, "jedna": 1, "jedno": 1, "dva": 2, "dvě": 2, "tři": 3, "čtyři": 4, "pět": 5,
    "šest": 6, "sedm": 7, "osm": 8, "devět": 9, "deset": 10, "jedenáct": 11, "dvanáct": 12,
    "třináct": 13, "čtrnáct": 14, "patnáct": 15, "šestnáct": 16, "sedmnáct": 17,
    "osmnáct": 18, "devatenáct": 19, "dvacet": 20, "třicet": 30, "čtyřicet": 40,
    "padesát": 50, "šedesát": 60, "sedmdesát": 70, "osmdesát": 80, "devadesát": 90,
    "sto": 100, "dvěstě": 200, "tisíc": 1000, "metr": 1, "metry": 1, "metrů": 1,
    "půl": Decimal("0.5"), "pár": 2,
}  # fmt: skip
_SCALES = (Decimal(1), Decimal(10), Decimal(100), Decimal(1000))
"""Převody na mm: mm, cm, dm, m (délky se v zadání píšou ve všech)."""


def numbers_in(text: str) -> set[Decimal]:
    """Čísla v textu: číslice (i s mezerou tisíců a desetinnou čárkou) a česká slova."""
    found: set[Decimal] = set()
    for token in _NUMBER.findall(text):
        clean = re.sub(r"\s", "", token).replace(",", ".")
        try:
            found.add(Decimal(clean))
        except InvalidOperation:  # pragma: no cover - regulární výraz to vylučuje
            continue
    words = re.findall(r"[a-záčďéěíňóřšťúůýž]+", text.lower())
    values = [Decimal(_WORDS[word]) for word in words if word in _WORDS]
    found |= set(values)
    # „dvacet pět“: součet sousedních slov
    found |= {a + b for a, b in pairwise(values)}
    # „metr dvacet“, „dva metry padesát“ = 1,20 m, 2,50 m
    for index, word in enumerate(words[:-1]):
        following = _WORDS.get(words[index + 1])
        if word.startswith("metr") and following is not None and Decimal(following) < 100:
            previous = _WORDS.get(words[index - 1]) if index > 0 else None
            whole = Decimal(previous) if previous is not None and not word.endswith("r") else 1
            found.add(whole + Decimal(following) / 100)
    return found


def project_numbers(project: Project | None) -> set[Decimal]:
    """Čísla potvrzené zakázky: navazující změna je smí převzít beze změny."""
    if project is None:
        return set()
    problem = project.problem
    params = project.parameters
    found = {Decimal(part.length_mm) for part in problem.parts}
    found |= {Decimal(part.quantity) for part in problem.parts}
    found |= {Decimal(stock.length_mm) for stock in problem.stock}
    found |= {stock.price for stock in problem.stock if stock.price is not None}
    found |= {params.kerf_mm, params.trim_mm, Decimal(params.min_remnant_mm)}
    return found


def anchored_length(value: Decimal, source: set[Decimal]) -> bool:
    """Délka v mm má oporu: je ve zdroji jako mm, cm, dm nebo m."""
    return any(value == number * scale for number in source for scale in _SCALES)


def anchored(value: Decimal, source: set[Decimal]) -> bool:
    """Počet nebo cena má oporu: je ve zdroji přímo."""
    return value in source


def proposal_numbers(proposal: ChangeProposal) -> set[Decimal]:
    """Čísla, o kterých smí mluvit odpověď asistenta: hodnoty návrhu a počty řádků."""
    found: set[Decimal] = {Decimal(len(proposal.parts)), Decimal(len(proposal.stock))}
    pieces = sum(part.quantity or 0 for part in proposal.parts)
    found.add(Decimal(pieces))
    for part in proposal.parts:
        found |= {Decimal(v) for v in (part.length_mm, part.quantity) if v is not None}
    for stock in proposal.stock:
        if stock.length_mm is not None:
            found.add(Decimal(stock.length_mm))
        if stock.price is not None:
            found.add(stock.price)
    params = proposal.parameters
    found |= {Decimal(v) for v in (params.kerf_mm, params.trim_mm) if v is not None}
    if params.min_remnant_mm is not None:
        found.add(Decimal(params.min_remnant_mm))
    return found


def grounded_reply(reply: str, proposal: ChangeProposal) -> bool:
    """Každé číslo v odpovědi asistenta je v návrhu (i jako cm nebo m)."""
    allowed = proposal_numbers(proposal)
    return all(
        number in allowed or any(number * scale in allowed for scale in _SCALES)
        for number in numbers_in(reply)
    )
