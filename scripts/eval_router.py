"""Evaluace routeru nad portem `Router` (spec kap. 9, skill `ai-evaluace`, ADR-0012).

    uv run --env-file .env python scripts/eval_router.py --set dev --routers jev,llm
    uv run python scripts/eval_router.py --from-raw evals/reports/raw/<soubor>.json

Volá placená API (TypeSafe, Groq); spouští se jen na pokyn autora. `--set test` jen
k měření, nikdy k ladění. Výsledek: surová data do `evals/reports/raw/` a metriky
v Markdownu na výstup (přesnost s 95% Wilsonovým intervalem, matice záměn, chyby).
"""

import argparse
import json
import os
import time
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from decision_engine.adapters.config import build_ai_adapters
from decision_engine.adapters.jev_router import JevRouter
from decision_engine.adapters.llm_router import LlmRouter
from decision_engine.app.ports import Router, RoutingRequest
from decision_engine.core.result import Err, Ok
from decision_engine.core.routing import NO_ORDER, RouteOutcome, RoutingDecision
from eval_stats import interval

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "evals" / "reports" / "raw"


def label(decision: RoutingDecision) -> str:
    """Rozhodnutí ve stejných hodnotách jako `expected.capability` v sadách."""
    if decision.outcome is RouteOutcome.SUPPORTED:
        return decision.capability or "cutting_1d"
    return decision.outcome.value


def routers(names: list[str]) -> dict[str, Router]:
    ai = build_ai_adapters()
    available: dict[str, Router] = {}
    if "jev" in names:
        available["jev"] = JevRouter.create(os.environ["TYPESAFE_API_KEY"])
    if "llm" in names:
        available["llm"] = LlmRouter(ai.llm, ai.prompts)
    return available


def run(cases: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, router in routers(names).items():
        for case in cases:
            order = case["input"]["order"]
            request = RoutingRequest(
                message=case["input"]["message"],
                order={"rozpracovana_zakazka": order if order is not None else NO_ORDER},
            )
            start = time.perf_counter()
            match router.route(request):
                case Ok(decision):
                    got, intent, error = label(decision), decision.intent, None
                case Err(failure):
                    got, intent, error = "error", None, failure.detail
            records.append(
                {
                    "case_id": case["id"],
                    "router": name,
                    "expected": case["expected"],
                    "got": got,
                    "intent": intent,
                    "error": error,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1),
                    "tags": case.get("tags", []),
                }
            )
    return records


def report(records: list[dict[str, Any]], case_set: str) -> str:
    lines = [f"# Router – sada `{case_set}`", ""]
    for name in sorted({r["router"] for r in records}):
        mine = [r for r in records if r["router"] == name]
        correct = sum(r["got"] == r["expected"]["capability"] for r in mine)
        latencies = sorted(r["latency_ms"] for r in mine)
        p50 = latencies[len(latencies) // 2] if latencies else 0
        lines += [
            f"## {name}",
            "",
            f"- Správně: {interval(correct, len(mine))}",
            f"- Latence p50: {p50} ms",
            "",
            "| očekáváno → rozhodnuto | počet |",
            "|---|---|",
        ]
        confusion = Counter((r["expected"]["capability"], r["got"]) for r in mine)
        lines += [f"| {exp} → {got} | {n} |" for (exp, got), n in sorted(confusion.items())]
        wrong = [r for r in mine if r["got"] != r["expected"]["capability"]]
        if wrong:
            lines += ["", "Chybné případy: " + ", ".join(r["case_id"] for r in wrong)]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", choices=("dev", "test"), default="dev")
    parser.add_argument("--routers", default="jev,llm")
    parser.add_argument("--from-raw", type=Path)
    args = parser.parse_args()
    if args.from_raw:
        data = json.loads(args.from_raw.read_text(encoding="utf-8"))
        print(report(data["records"], data["set"]))
        return
    cases_path = ROOT / "evals" / "router" / args.set / "cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    records = run(cases, [name.strip() for name in args.routers.split(",") if name.strip()])
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(tz=UTC).date().isoformat()
    out = RAW_DIR / f"{today}-router-{args.set}-{uuid.uuid4().hex[:6]}.json"
    payload = {"set": args.set, "date": today, "records": records}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report(records, args.set))
    print(f"\nSurová data: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
