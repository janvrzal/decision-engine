"""Spike #7: zvládne TypeSafe Jev routing českých zadání? Prototyp mimo `src/`.

    uv run --group router-spike --env-file .env python scripts/spike_router.py
    uv run --group router-spike python scripts/spike_router.py --from-raw <soubor.jsonl>

Pustí dev sadu `evals/router/dev/cases.json` přes několik variant otázek, uloží surové
odpovědi (payload, pravděpodobnosti, latence, tokeny) do JSONL a vypíše metriky v Markdownu.
`--from-raw` přepočítá metriky ze surových odpovědí bez volání API.

Jev dělá úsudky (jaká práce, je zadání konkrétní, co chce s rozpracovanou zakázkou),
rozhodnutí o schopnosti a záměru dělá kód v `decide_*` (pravdivostní tabulka).
Produkční `JevRouter` vznikne až v M3; tady jde jen o měření. Sada `evals/router/test/`
se tu nepoužívá.
"""

import argparse
import json
import statistics
import time
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from typesafe_sdk import Choice, Noul, NoulCriteria, RetryPolicy, TypeSafeClient

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "router" / "dev" / "cases.json"
MODEL = "jev-1.14.0"
NO_ORDER = "žádná – uživatel zatím nic nezadal"

# Prahy (výchozí hodnoty ze skillu TypeSafe; ladí se jen na dev sadě).
NOUL_YES = 0.7
NOUL_NO = 0.3
MIN_TOP_PROBABILITY = 0.5

Questions = dict[str, Choice | Noul]
Answers = dict[str, Any]

# --- Znění otázek: vše na jednom místě ------------------------------------------

TASK_CS = {
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
TASK_EN = {
    "cutting_bars": (
        "Cut bars, profiles, tubes or battens into pieces of given lengths, change the parts "
        "or stock of the current order, or ask about its cutting plan and waste"
    ),
    "pricing": "Find out the price, costs or cost estimate of the order",
    "cutting_sheets": "Lay out rectangular parts on boards or metal sheets",
    "packing": "Pack items into boxes, crates or a vehicle",
    "other_request": (
        "Something else: making a whole product, an invoice, tiles, a greeting "
        "or a question unrelated to the workshop"
    ),
}
INTENT_CS = {
    "new_order": "Začít úplně jinou zakázku s novými díly",
    "change_order": "Změnit díly, materiál, nastavení nebo vstupy kalkulace rozpracované zakázky",
    "result_question": "Zeptat se na spočítaný plán nebo jeho cenu, aniž by cokoli měnil",
}
INTENT_EN = {
    "new_order": "Start a completely different order with new parts",
    "change_order": "Change the parts, stock, settings or cost inputs of the current order",
    "result_question": "Ask about the computed plan or its price without changing anything",
}


def task_cs(criteria: Mapping[str, str] = TASK_CS) -> Questions:
    return {
        "task": Choice(
            instructions="Jakou práci chce uživatel ve zprávě `zprava` od aplikace pro dílnu?",
            criteria=dict(criteria),
        ),
        "concrete": Noul(
            instructions=(
                "Je ze zprávy `zprava` jasné, co má aplikace spočítat, změnit nebo vysvětlit?"
            ),
            criteria=NoulCriteria(
                true=(
                    "Zpráva uvádí, co se má spočítat nebo změnit: délky a počty dílů, novou "
                    "hodnotu nastavení nebo otázku na cenu či odpad rozpracované zakázky."
                ),
                false=(
                    "Zpráva jen naznačuje záměr nebo pozdravuje, například „chci udělat stůl“ "
                    "nebo „potřebuju to nějak spočítat“, a nedá se z ní poznat, co spočítat."
                ),
            ),
        ),
        "intent": Choice(
            instructions="Co chce uživatel zprávou `zprava` udělat s `rozpracovana_zakazka`?",
            criteria=dict(INTENT_CS),
        ),
    }


def task_en() -> Questions:
    return {
        "task": Choice(
            instructions="What work does the user want from the workshop app in `zprava`?",
            criteria=dict(TASK_EN),
        ),
        "concrete": Noul(
            instructions=(
                "Does `zprava` make clear what the app should calculate, change or explain?"
            ),
            criteria=NoulCriteria(
                true=(
                    "The message states what to calculate or change: part lengths and counts, "
                    "a new setting value, or a question about the price or waste "
                    "of the current order."
                ),
                false=(
                    "The message only hints at a goal or greets, for example 'I want to make a "
                    "table' or 'I need to work something out', and does not say what to calculate."
                ),
            ),
        ),
        "intent": Choice(
            instructions="What does the user want to do with `rozpracovana_zakazka` in `zprava`?",
            criteria=dict(INTENT_EN),
        ),
    }


def task_cs_v2() -> Questions:
    """2. iterace: Noul o konkrétnosti nezávislý na tom, zda úlohu aplikace umí."""
    questions = task_cs()
    questions["concrete"] = Noul(
        instructions="Říká zpráva `zprava` konkrétně, co má aplikace udělat?",
        criteria=NoulCriteria(
            true=(
                "Zpráva uvádí konkrétní úkol, i když ho aplikace pro dílnu neumí: díly k nařezání, "
                "změnu zakázky, dotaz na cenu nebo odpad, nebo jakýkoli jiný jasný požadavek."
            ),
            false=(
                "Zpráva jen naznačuje cíl nebo pozdravuje, například „chci udělat stůl“ nebo "
                "„potřebuju to nějak spočítat“, a není z ní jasné, co má aplikace udělat."
            ),
        ),
    )
    return questions


def naive_cs() -> Questions:
    """Jedna otázka přímo nad množinou ze specifikace (kap. 6) jako srovnání."""
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
        "intent": Choice(
            instructions="Co chce uživatel zprávou `zprava` udělat s `rozpracovana_zakazka`?",
            criteria=dict(INTENT_CS),
        ),
    }


# --- Rozhodnutí v kódu ----------------------------------------------------------

TASK_TO_CAPABILITY = {
    "cutting_bars": "cutting_1d",
    "pricing": "cost_estimate",
    "cutting_sheets": "unsupported",
    "packing": "unsupported",
    "other_request": "unsupported",
}


def top(answer: Answers) -> tuple[str, float]:
    choice = str(answer["choice"])
    return choice, float(answer["probabilities"][choice])


def decide_intent(answers: Mapping[str, Answers], has_order: bool) -> str:
    # Bez rozpracované zakázky je záměr vždy nová zakázka; to ví kód, ne model.
    return top(answers["intent"])[0] if has_order else "new_order"


def decide_decomposed(answers: Mapping[str, Answers], has_order: bool) -> tuple[str, str]:
    task, p_task = top(answers["task"])
    concrete = float(answers["concrete"]["noul"])
    if concrete < NOUL_YES or p_task < MIN_TOP_PROBABILITY:
        # 1. iterace: ne i nerozhodnuté pásmo → doptat se, bez ohledu na druh úlohy.
        return "unclear", decide_intent(answers, has_order)
    return TASK_TO_CAPABILITY[task], decide_intent(answers, has_order)


def decide_v2(answers: Mapping[str, Answers], has_order: bool) -> tuple[str, str]:
    """Pravdivostní tabulka 2. iterace.

    | task                     | concrete ≥ 0,7 | 0,3–0,7      | < 0,3   |
    | cutting_bars             | cutting_1d     | cutting_1d   | unclear |
    | pricing                  | cost_estimate  | cost_estimate| cost_estimate |
    | cutting_sheets, packing  | unsupported    | unsupported  | unsupported |
    | other_request            | unsupported    | unclear      | unclear |

    U řezání chybějící údaje dohledá extrakce podle schématu (spec kap. 6), u ceny bez plánu
    aplikace nabídne nejdřív plán; Noul proto rozhoduje jen „nejasné × mimo rozsah“.
    """
    task, p_task = top(answers["task"])
    concrete = float(answers["concrete"]["noul"])
    intent = decide_intent(answers, has_order)
    if p_task < MIN_TOP_PROBABILITY:
        return "unclear", intent
    if task == "cutting_bars" and concrete < NOUL_NO:
        return "unclear", intent
    if task == "other_request" and concrete < NOUL_YES:
        return "unclear", intent
    return TASK_TO_CAPABILITY[task], intent


def decide_naive(answers: Mapping[str, Answers], has_order: bool) -> tuple[str, str]:
    capability, p_top = top(answers["capability"])
    if p_top < MIN_TOP_PROBABILITY:
        capability = "unclear"
    return capability, decide_intent(answers, has_order)


@dataclass(frozen=True)
class Variant:
    questions: Callable[[], Questions]
    decide: Callable[[Mapping[str, Answers], bool], tuple[str, str]]
    top_question: str


VARIANTS: dict[str, Variant] = {
    "naive_cs": Variant(naive_cs, decide_naive, "capability"),
    "decomposed_cs": Variant(task_cs, decide_decomposed, "task"),
    "decomposed_cs_reversed": Variant(
        lambda: task_cs(dict(reversed(TASK_CS.items()))), decide_decomposed, "task"
    ),
    "decomposed_en": Variant(task_en, decide_decomposed, "task"),
    "decomposed_cs_v2": Variant(task_cs_v2, decide_v2, "task"),
}


# --- Běh ------------------------------------------------------------------------


def build_state(case_input: Mapping[str, Any]) -> dict[str, Any]:
    order = case_input["order"]
    return {"zprava": case_input["message"], "rozpracovana_zakazka": order or NO_ORDER}


def run(cases: list[dict[str, Any]], out: Path, variants: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    retry = RetryPolicy(max_retries=2)
    start = time.perf_counter()
    with TypeSafeClient(model=MODEL, retry=retry) as client, out.open("w") as sink:
        for case in cases:
            for name in variants:
                questions = VARIANTS[name].questions()
                if case["input"]["order"] is None:
                    questions.pop("intent")
                state = build_state(case["input"])
                t0 = time.perf_counter()
                # Typ `state` v SDK obsahuje rekurzivní alias, který pyright neumí plně odvodit.
                response = client.system_one(  # pyright: ignore[reportUnknownMemberType]
                    state=state, questions=questions
                )
                latency_ms = (time.perf_counter() - t0) * 1000
                record = {
                    "case_id": case["id"],
                    "variant": name,
                    "model": response.model,
                    "request": {
                        "state": state,
                        "questions": {k: q.model_dump(mode="json") for k, q in questions.items()},
                    },
                    "answers": {k: a.model_dump(mode="json") for k, a in response.answers.items()},
                    "usage": response.usage.model_dump(mode="json"),
                    "latency_ms": round(latency_ms, 1),
                    "first_call": not records,
                }
                records.append(record)
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Celkový čas běhu: {time.perf_counter() - start:.1f} s, volání: {len(records)}")
    return records


# --- Metriky --------------------------------------------------------------------


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def report(cases: list[dict[str, Any]], records: list[dict[str, Any]]) -> None:
    by_id = {case["id"]: case for case in cases}
    labels = ["cutting_1d", "cost_estimate", "unclear", "unsupported"]
    print(f"Model: {sorted({r['model'] for r in records})}, případů: {len(cases)}")
    print("Rozložení:", dict(Counter(c["expected"]["capability"] for c in cases)))
    first = [r["latency_ms"] for r in records if r["first_call"]]
    print(f"První volání (studený start spojení): {first} ms\n")
    print("| Varianta | Schopnost | Záměr (se zakázkou) | Latence medián / p95 | Vstupní tokeny |")
    print("|---|---|---|---|---|")
    errors: list[str] = []
    bands: dict[str, Counter[tuple[str, bool]]] = {}
    confusion: dict[str, Counter[tuple[str, str]]] = {}
    for name in VARIANTS:
        rows = [r for r in records if r["variant"] == name and not r["first_call"]]
        rows_all = [r for r in records if r["variant"] == name]
        if not rows_all:
            continue
        ok = intent_ok = intent_n = tokens = 0
        bands[name] = Counter()
        confusion[name] = Counter()
        for r in rows_all:
            case = by_id[r["case_id"]]
            has_order = case["input"]["order"] is not None
            capability, intent = VARIANTS[name].decide(r["answers"], has_order)
            expected = case["expected"]
            hit = capability == expected["capability"]
            ok += hit
            confusion[name][(expected["capability"], capability)] += 1
            _, p_top = top(r["answers"][VARIANTS[name].top_question])
            band = "≥0,9" if p_top >= 0.9 else "0,7–0,9" if p_top >= 0.7 else "<0,7"
            bands[name][(band, hit)] += 1
            if has_order and expected["intent"] is not None:
                intent_n += 1
                intent_ok += intent == expected["intent"]
            tokens += int(r["usage"].get("input_tokens") or 0)
            if not hit or (has_order and expected["intent"] not in (None, intent)):
                detail = {
                    k: v.get("probabilities") or v.get("noul") for k, v in r["answers"].items()
                }
                errors.append(
                    f"- `{name}` {r['case_id']} „{case['input']['message']}“: "
                    f"čekáno {expected['capability']}/{expected['intent']}, "
                    f"vyšlo {capability}/{intent}; {json.dumps(detail, ensure_ascii=False)}"
                )
        latencies = [r["latency_ms"] for r in rows] or [0.0]
        print(
            f"| {name} | {ok}/{len(rows_all)} ({ok / len(rows_all):.0%}) "
            f"| {intent_ok}/{intent_n} "
            f"| {statistics.median(latencies):.0f} / {percentile(latencies, 0.95):.0f} ms "
            f"| {tokens / len(rows_all):.0f} / volání |"
        )
    print("\n## Kalibrace (přesnost schopnosti podle pravděpodobnosti hlavní volby)\n")
    for name, counter in bands.items():
        parts: list[str] = []
        for band in ("≥0,9", "0,7–0,9", "<0,7"):
            hit, miss = counter[(band, True)], counter[(band, False)]
            if hit + miss:
                parts.append(f"{band}: {hit}/{hit + miss}")
        print(f"- `{name}`: " + ", ".join(parts))
    print("\n## Matice záměn (řádek = očekáváno, sloupec = vyšlo)\n")
    for name, counter in confusion.items():
        print(f"`{name}`\n\n| | " + " | ".join(labels) + " |\n|---" * (len(labels) + 1) + "|")
        for expected in labels:
            cells = " | ".join(str(counter[(expected, got)]) for got in labels)
            print(f"| {expected} | {cells} |")
        print()
    print("## Chyby\n")
    print("\n".join(errors) or "žádné")


def main() -> None:
    parser = argparse.ArgumentParser(description="Spike #7: routing českých zadání přes Jev.")
    parser.add_argument("--from-raw", type=Path, help="přepočítat metriky z JSONL bez API")
    parser.add_argument("--out", type=Path, default=Path("spike-router-raw.jsonl"))
    parser.add_argument("--variant", action="append", choices=list(VARIANTS))
    args = parser.parse_args()
    cases: list[dict[str, Any]] = json.loads(CASES.read_text())
    if args.from_raw:
        records = [json.loads(line) for line in args.from_raw.read_text().splitlines()]
    else:
        records = run(cases, args.out, args.variant or list(VARIANTS))
    report(cases, records)


if __name__ == "__main__":
    main()
