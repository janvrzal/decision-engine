"""Znění otázek pro Jev a pravdivostní tabulky rozhodnutí (spike #7, ADR-0012).

Všechno, co se u routeru Jev ladí a audituje, je na jednom místě: otázky, kritéria,
prahy a převod úsudků na rozhodnutí. Jev dělá úsudky, rozhodnutí dělá kód.
Varianty jsou změřené na `evals/router/dev`; výchozí určí měření na test sadě.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from typesafe_sdk import Choice, Noul, NoulCriteria

MODEL = "jev-1.14.0"
NOUL_YES = 0.7
NOUL_NO = 0.3
MIN_TOP_PROBABILITY = 0.9
"""Práh pravděpodobnosti nejlepší volby (ADR-0004, dodatek ze spiku): pod ním „unclear“."""

type Questions = dict[str, Choice | Noul]
type Answers = Mapping[str, Any]
type Decision = tuple[str, str | None]
"""(capability nebo `unclear`/`unsupported`, intent)."""

INTENT = {
    "new_order": "Začít úplně jinou zakázku s novými díly",
    "change_order": "Změnit díly, materiál, nastavení nebo vstupy kalkulace rozpracované zakázky",
    "result_question": "Zeptat se na spočítaný plán nebo jeho cenu, aniž by cokoli měnil",
}

TASK = {
    "cutting_bars": (
        "Nařezat tyče, profily, trubky, jekly nebo latě na kusy daných délek, upravit díly "
        "či materiál rozpracované zakázky nebo se zeptat na její nářezový plán a odpad"
    ),
    "pricing": "Zjistit cenu, náklady nebo kalkulaci zakázky",
    "cutting_sheets": "Rozvrhnout obdélníkové díly na desky nebo plechy",
    "packing": "Naskládat předměty do krabic, beden nebo vozidla",
    "other_request": (
        "Něco jiného: výroba celého výrobku, faktura, obklady, pozdrav nebo dotaz mimo dílnu"
    ),
}
TASK_TO_CAPABILITY = {
    "cutting_bars": "cutting_1d",
    "pricing": "cost_estimate",
    "cutting_sheets": "unsupported",
    "packing": "unsupported",
    "other_request": "unsupported",
}


def _intent() -> Choice:
    return Choice(
        instructions="Co chce uživatel zprávou `zprava` udělat s `rozpracovana_zakazka`?",
        criteria=dict(INTENT),
    )


def naive_questions() -> Questions:
    """Jedna volba přímo nad množinou ze specifikace (kap. 6) a záměr."""
    return {
        "capability": Choice(
            instructions="Jakou úlohu chce uživatel ve zprávě `zprava` od aplikace pro dílnu?",
            criteria={
                "cutting_1d": (
                    "Řezání tyčí, profilů nebo trubek na kusy daných délek (nářezový plán), "
                    "včetně úprav a dotazů k rozpracované zakázce"
                ),
                "cost_estimate": "Cena, náklady nebo kalkulace zakázky",
                "unclear": "Ze zprávy nejde poznat, co má aplikace spočítat",
                "unsupported": (
                    "Úloha, kterou aplikace neumí: desky, skládání, faktury, obklady, "
                    "dotazy mimo dílnu"
                ),
            },
        ),
        "intent": _intent(),
    }


def decomposed_questions() -> Questions:
    """Druh práce, konkrétnost zprávy (Noul) a záměr; rozhodnutí v `decide_decomposed`."""
    return {
        "task": Choice(
            instructions="Jakou práci chce uživatel ve zprávě `zprava` od aplikace pro dílnu?",
            criteria=dict(TASK),
        ),
        "concrete": Noul(
            instructions="Říká zpráva `zprava` konkrétně, co má aplikace udělat?",
            criteria=NoulCriteria(
                true=(
                    "Zpráva uvádí konkrétní úkol, i když ho aplikace pro dílnu neumí: díly "
                    "k nařezání, změnu zakázky, dotaz na cenu nebo odpad, nebo jakýkoli jiný "
                    "jasný požadavek."
                ),
                false=(
                    "Zpráva jen naznačuje cíl nebo pozdravuje, například „chci udělat stůl“ "
                    "nebo „potřebuju to nějak spočítat“, a není z ní jasné, co má aplikace udělat."
                ),
            ),
        ),
        "intent": _intent(),
    }


def _top(answer: Answers) -> tuple[str, float]:
    choice = str(answer["choice"])
    return choice, float(answer["probabilities"][choice])


def _intent_of(answers: Mapping[str, Answers], has_order: bool) -> str | None:
    # Bez rozpracované zakázky je záměr vždy nová zakázka; to ví kód, ne model.
    return _top(answers["intent"])[0] if has_order and "intent" in answers else "new_order"


def decide_naive(answers: Mapping[str, Answers], has_order: bool) -> Decision:
    capability, probability = _top(answers["capability"])
    if probability < MIN_TOP_PROBABILITY:
        capability = "unclear"
    return capability, _intent_of(answers, has_order)


def decide_decomposed(answers: Mapping[str, Answers], has_order: bool) -> Decision:
    """Pravdivostní tabulka (spike, 2. iterace).

    | task                    | concrete ≥ 0,7 | 0,3–0,7       | < 0,3         |
    | cutting_bars            | cutting_1d     | cutting_1d    | unclear       |
    | pricing                 | cost_estimate  | cost_estimate | cost_estimate |
    | cutting_sheets, packing | unsupported    | unsupported   | unsupported   |
    | other_request           | unsupported    | unclear       | unclear       |
    """
    task, probability = _top(answers["task"])
    concrete = float(answers["concrete"]["noul"])
    intent = _intent_of(answers, has_order)
    if probability < MIN_TOP_PROBABILITY:
        return "unclear", intent
    if task == "cutting_bars" and concrete < NOUL_NO:
        return "unclear", intent
    if task == "other_request" and concrete < NOUL_YES:
        return "unclear", intent
    return TASK_TO_CAPABILITY[task], intent


@dataclass(frozen=True, slots=True)
class Variant:
    questions: Callable[[], Questions]
    decide: Callable[[Mapping[str, Answers], bool], Decision]


VARIANTS: dict[str, Variant] = {
    "naive_cs": Variant(naive_questions, decide_naive),
    "decomposed_cs_v2": Variant(decomposed_questions, decide_decomposed),
}
DEFAULT_VARIANT = "naive_cs"
