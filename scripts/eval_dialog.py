"""Evaluace vícekolového dialogu (spec kap. 9: 10 scénářů × 3 kola, skill `ai-evaluace`).

    uv run --env-file .env python scripts/eval_dialog.py --set dev
    uv run python scripts/eval_dialog.py --from-raw evals/reports/raw/<soubor>.json

Každý scénář projde skutečnou cestou aplikace (`handle`: router → extrakce → potvrzení
→ výpočet) s adaptéry z prostředí; volá placená API, spouští se jen na pokyn autora.
Po každém kole se porovná výsledek (podporované / nejasné / nepodporované) a u
podporovaného kola stav zakázky po potvrzení s očekáváním. Materiál se porovnává jen
podle toho, zda je vyplněný (význam profilu posoudí člověk v surových datech).
`--set test` jen k měření, nikdy k ladění.
"""

import argparse
import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from decision_engine.adapters.config import build_ai_adapters
from decision_engine.app.ports import Ports
from decision_engine.app.session import handle
from decision_engine.app.solving import RegistrySolver
from decision_engine.core.events import MessageSent, ProposalConfirmed
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.routing import UNSUPPORTED_TEXT
from decision_engine.core.state import AppState, initial_state
from eval_stats import interval

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "evals" / "reports" / "raw"


def snapshot(project: Project | None) -> dict[str, Any] | None:
    """Zakázka ve tvaru očekávání ze sad (pořadí řádků nehraje roli)."""
    if project is None:
        return None
    params = project.parameters
    return {
        "material": project.problem.material,
        "parts": sorted([p.length_mm, p.quantity] for p in project.problem.parts),
        "stock": sorted(
            [s.length_mm, str(s.price) if s.price is not None else None]
            for s in project.problem.stock
        ),
        "kerf_mm": str(params.kerf_mm),
        "trim_mm": str(params.trim_mm),
        "min_remnant_mm": params.min_remnant_mm,
    }


def matches(expected: dict[str, Any] | None, got: dict[str, Any] | None) -> list[str]:
    """Chybná pole zakázky po kole; prázdný seznam = shoda."""
    if expected is None:
        return []
    if got is None:
        return ["zakazka_chybi"]
    errors: list[str] = []
    if sorted([p["length_mm"], p["quantity"]] for p in expected["parts"]) != got["parts"]:
        errors.append("parts")
    want_stock = sorted(
        [s["length_mm"], str(Decimal(s["price"])) if s["price"] is not None else None]
        for s in expected["stock"]
    )
    got_stock = [[length, str(Decimal(price)) if price else None] for length, price in got["stock"]]
    if expected["stock"] and want_stock != got_stock:
        errors.append("stock")
    for name in ("kerf_mm", "trim_mm"):
        if expected.get(name) is not None and Decimal(str(expected[name])) != Decimal(got[name]):
            errors.append(name)
    remnant = expected.get("min_remnant_mm")
    if remnant is not None and remnant != got["min_remnant_mm"]:
        errors.append("min_remnant_mm")
    if (expected.get("material") is None) != (got["material"] is None):
        errors.append("material")
    return errors


def outcome(before: AppState, after: AppState) -> str:
    """Co aplikace se zprávou udělala: návrh, doptání, odmítnutí, nebo chyba."""
    if after.proposal is not None and after.proposal != before.proposal:
        return "supported"
    last = after.messages[-1] if after.messages else None
    if last is not None and last.kind == "error":
        return "error"
    if last is not None and last.offer_manual:
        return "unsupported" if last.text == UNSUPPORTED_TEXT else "unclear"
    return "supported"


def run_scenario(scenario: dict[str, Any], ports: Ports) -> list[dict[str, Any]]:
    state = initial_state(f"eval-{uuid.uuid4().hex[:8]}")
    turns: list[dict[str, Any]] = []
    for index, turn in enumerate(scenario["turns"]):
        before = state
        state = handle(state, MessageSent(text=turn["input"]), ports)
        got = outcome(before, state)
        if got == "supported" and state.proposal is not None:
            state = handle(state, ProposalConfirmed(), ports)
        expected = turn["expected"]
        errors = [] if got == expected["outcome"] else [f"outcome:{got}"]
        if got == expected["outcome"] == "supported":
            errors += matches(expected.get("project"), snapshot(state.project))
        turns.append(
            {
                "scenario": scenario["id"],
                "turn": index + 1,
                "expected_outcome": expected["outcome"],
                "outcome": got,
                "project": snapshot(state.project),
                "errors": errors,
            }
        )
    return turns


def report(records: list[dict[str, Any]], case_set: str) -> str:
    correct = sum(not r["errors"] for r in records)
    scenarios = sorted({r["scenario"] for r in records})
    whole = sum(all(not r["errors"] for r in records if r["scenario"] == s) for s in scenarios)
    lines = [
        f"# Dialog – sada `{case_set}`",
        "",
        f"- Správná kola: {interval(correct, len(records))}",
        f"- Scénáře bez chyby: {whole}/{len(scenarios)}",
        "",
        "| Scénář | Kolo | Očekáváno | Výsledek | Chyby |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {r['scenario']} | {r['turn']} | {r['expected_outcome']} | {r['outcome']} | "
        f"{', '.join(r['errors']) or '–'} |"
        for r in records
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=("dev", "test"), default="dev")
    parser.add_argument("--from-raw", type=Path)
    args = parser.parse_args()
    if args.from_raw:
        data = json.loads(args.from_raw.read_text(encoding="utf-8"))
        print(report(data["records"], data["set"]))
        return
    ai = build_ai_adapters()
    ports = Ports(
        llm=ai.llm, prompts=ai.prompts, tracer=ai.tracer, solver=RegistrySolver(), router=ai.router
    )
    paths = sorted((ROOT / "evals" / "dialog" / args.set).glob("*.json"))
    records: list[dict[str, Any]] = []
    for path in paths:
        records += run_scenario(json.loads(path.read_text(encoding="utf-8")), ports)
    ai.tracer.flush()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=UTC).date().isoformat()
    out = RAW_DIR / f"{today}-dialog-{args.set}-{uuid.uuid4().hex[:6]}.json"
    out.write_text(
        json.dumps(
            {"set": args.set, "date": today, "records": records}, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(report(records, args.set))
    print(f"\nSurová data: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
