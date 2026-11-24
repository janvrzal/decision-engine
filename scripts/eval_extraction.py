"""Evaluace extrakce 1D zakázky na více modelech (skill `ai-evaluace`, ADR-0008, #6).

    uv run --env-file .env python scripts/eval_extraction.py \
        [--set dev] [--models openai/gpt-oss-120b,...] [--format json_object|json_schema] \
        [--limit N] [--from-raw evals/reports/raw/<soubor>.json]

Každý případ projde stejnou cestou jako v aplikaci (`handle` → `run_extraction` →
`OpenAICompatibleLlm`, prompt `extract-proposal-1d` z Langfuse nebo zálohy) včetně
jednoho opravného pokusu. Trasování do Langfuse zůstává zapnuté; session = běh evaluace
pro jeden model. Surové výsledky se uloží do `evals/reports/raw/` a z nich se vypíšou
tabulky pro report; `--from-raw` přepočítá tabulky bez volání modelu.

Ve výchozím běhu se volá placené API: spouštět jen na pokyn uživatele. Model lze zvolit
i proměnnou `LLM_MODEL`, když není zadaný `--models`. Sada `test` je jen pro měření.
"""

import argparse
import hashlib
import importlib
import json
import os
import re
import statistics
import time
import uuid
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from decision_engine.adapters.config import DEFAULT_BASE_URL, build_ai_adapters
from decision_engine.adapters.llm_openai import MAX_RETRIES, TIMEOUT_SECONDS, OpenAICompatibleLlm
from decision_engine.app.ports import ChatMessage, LlmError, Ports, Prompt
from decision_engine.app.session import handle
from decision_engine.app.solving import RegistrySolver
from decision_engine.core.events import MessageSent
from decision_engine.core.extraction import ExtractionOutput, proposal_from_extraction
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.state import initial_state
from eval_stats import interval, mcnemar

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "evals" / "reports"
DEFAULT_MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b")
PRICES_USD_PER_MTOK: dict[str, tuple[Decimal, Decimal]] = {
    # Ceník Groq ke 23. 11. 2026 (ADR-0009): vstup, výstup (reasoning tokeny jako výstup).
    "openai/gpt-oss-120b": (Decimal("0.15"), Decimal("0.60")),
    "openai/gpt-oss-20b": (Decimal("0.075"), Decimal("0.30")),
    "qwen/qwen3.8-27b": (Decimal("0.80"), Decimal("4.00")),
}
SCHEMA_VERSION = hashlib.sha256(
    json.dumps(ExtractionOutput.model_json_schema(), sort_keys=True).encode()
).hexdigest()[:12]
"""Otisk JSON schématu `ExtractionOutput` (verze schématu pro report)."""

FIELDS = ("parts", "stock_length", "stock_price", "kerf_mm", "trim_mm", "min_remnant_mm")
"""Kritická pole; `objective` se hodnotí zvlášť (není ve spec kap. 9 mezi kritickými)."""


# --- Záznam volání ------------------------------------------------------------------


@dataclass
class CallRecord:
    attempt: int
    latency_s: float
    ok: bool
    schema_valid: bool
    text: str | None
    error: str | None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    model_time_s: float | None = None
    """Čas zpracování na straně Groq (`usage.total_time`) bez čekání na limity a sítě."""


@dataclass
class CaseRecord:
    case_id: str
    model: str
    latency_s: float = 0.0
    calls: list[CallRecord] = field(default_factory=lambda: list[CallRecord]())
    prompt_version: int | None = None
    prompt_source: str = ""


class _Completions:
    """Obal `chat.completions` klienta: změří čas a uloží spotřebu tokenů."""

    def __init__(self, inner: Any, response_format: dict[str, Any] | None) -> None:
        self._inner = inner
        self._response_format = response_format
        self.last_usage: Any = None
        self.last_latency = 0.0

    def create(self, **kwargs: Any) -> Any:
        if self._response_format is not None:
            kwargs["response_format"] = self._response_format
        self.last_usage = None
        started = time.perf_counter()
        try:
            response = self._inner.chat.completions.create(**kwargs)
        finally:
            self.last_latency = time.perf_counter() - started
        self.last_usage = getattr(response, "usage", None)
        return response


class _Chat:
    def __init__(self, completions: _Completions) -> None:
        self.completions = completions


class _ClientProxy:
    def __init__(self, completions: _Completions) -> None:
        self.chat = _Chat(completions)


class RecordingLlm:
    """`LlmClient`, který zaznamená každé volání pro výpočet metrik."""

    def __init__(self, llm: OpenAICompatibleLlm, completions: _Completions) -> None:
        self._llm = llm
        self._completions = completions
        self.case: CaseRecord | None = None

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        result = self._llm.complete_json(messages, prompt=prompt, attempt=attempt)
        usage = self._completions.last_usage
        record = CallRecord(
            attempt=attempt,
            latency_s=self._completions.last_latency,
            ok=isinstance(result, Ok),
            schema_valid=False,
            text=None,
            error=None,
            prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            reasoning_tokens=_reasoning_tokens(usage),
            model_time_s=getattr(usage, "total_time", None),
        )
        match result:
            case Ok(text):
                record.text = text
                record.schema_valid = _valid(text)
            case Err(error):
                # Hláška Groq obsahuje id organizace; do repozitáře nepatří.
                detail = re.sub(r"org_\w+", "org_…", error.detail)
                record.error = f"{error.kind}: {detail[:300]}"
        if self.case is not None:
            self.case.calls.append(record)
            self.case.prompt_version = prompt.version
            self.case.prompt_source = prompt.source
        return result


def _reasoning_tokens(usage: Any) -> int:
    details = getattr(usage, "completion_tokens_details", None)
    return int(getattr(details, "reasoning_tokens", 0) or 0)


def _valid(text: str) -> bool:
    try:
        ExtractionOutput.model_validate_json(text)
    except ValidationError:
        return False
    return True


# --- Běh ---------------------------------------------------------------------------


def load_cases(set_name: str) -> list[dict[str, Any]]:
    folder = ROOT / "evals" / "extraction" / set_name
    return [
        cast(dict[str, Any], json.loads(path.read_text("utf-8")))
        for path in sorted(folder.glob("*.json"))
    ]


def run_model(
    model: str, cases: list[dict[str, Any]], run_id: str, response_format: str, pause: float
) -> list[CaseRecord]:
    ai = build_ai_adapters()
    traced = ai.langfuse_enabled
    client_class: Any = (
        importlib.import_module("langfuse.openai").OpenAI
        if traced
        else importlib.import_module("openai").OpenAI
    )
    inner = client_class(
        base_url=os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL,
        api_key=os.environ["LLM_API_KEY"],
        max_retries=MAX_RETRIES,
        timeout=TIMEOUT_SECONDS,
    )
    completions = _Completions(inner, _response_format(response_format))
    llm = RecordingLlm(
        OpenAICompatibleLlm(_ClientProxy(completions), model, traced=traced), completions
    )
    ports = Ports(llm=llm, prompts=ai.prompts, tracer=ai.tracer, solver=RegistrySolver())
    session_id = f"eval-extraction-{run_id}-{model.replace('/', '_')}"
    print(f"{model}: session {session_id} (Langfuse {'zapnutý' if traced else 'vypnutý'})")

    records: list[CaseRecord] = []
    for index, case in enumerate(cases):
        if index and pause:
            time.sleep(pause)  # Free tier Groq: limity tokenů za minutu (TPM, OTPM).
        record = CaseRecord(case_id=case["id"], model=model)
        llm.case = record
        started = time.perf_counter()
        handle(initial_state(session_id), MessageSent(text=case["input"]), ports)
        record.latency_s = time.perf_counter() - started
        records.append(record)
        print(f"  {case['id']}: {len(record.calls)} volání, {record.latency_s:.2f} s")
    ai.tracer.flush()
    return records


def _response_format(name: str) -> dict[str, Any] | None:
    if name == "json_object":
        return None  # Jako v aplikaci (adaptér posílá json_object).
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "extraction_output",
            "schema": ExtractionOutput.model_json_schema(),
            "strict": False,
        },
    }


# --- Hodnocení ---------------------------------------------------------------------


def final_output(record: CaseRecord) -> ExtractionOutput | None:
    for call in reversed(record.calls):
        if call.text is not None and call.schema_valid:
            return ExtractionOutput.model_validate_json(call.text)
    return None


def compare(expected: dict[str, Any], record: CaseRecord) -> list[str]:
    """Vrátí seznam chybných kritických polí (prázdný = úplná shoda)."""
    output = final_output(record)
    if output is None:
        return ["api_rate_limit" if rate_limited(record) else "neplatny_vystup"]
    errors: list[str] = []
    want_parts = sorted(((p["length_mm"], p["quantity"]) for p in expected["parts"]), key=_key)
    got_parts = sorted(((p.length_mm, p.quantity) for p in output.parts), key=_key)
    if len(want_parts) != len(got_parts):
        errors.append("parts_pocet_polozek")
    elif [p[0] for p in want_parts] != [p[0] for p in got_parts]:
        errors.append("parts_delka")
    elif want_parts != got_parts:
        errors.append("parts_pocet_kusu")
    want_stock = sorted(
        ((s["length_mm"], _money(s["price"])) for s in expected["stock"]), key=_stock_key
    )
    got_stock = sorted(((s.length_mm, s.price) for s in output.stock), key=_stock_key)
    if [s[0] for s in want_stock] != [s[0] for s in got_stock]:
        errors.append("stock_length")
    elif [s[1] for s in want_stock] != [s[1] for s in got_stock]:
        errors.append("stock_price")
    for name in ("kerf_mm", "trim_mm", "min_remnant_mm"):
        if expected[name] != getattr(output, name):
            errors.append(name)
    return errors


def hallucinated(expected: dict[str, Any], output: ExtractionOutput | None) -> bool:
    """Model vrátil hodnotu, kterou zadání neuvádí (očekávané `null` nebo prázdný sklad)."""
    if output is None:
        return False
    if not expected["stock"] and output.stock:
        return True
    return any(
        expected[name] is None and getattr(output, name) is not None
        for name in ("kerf_mm", "trim_mm", "min_remnant_mm")
    )


def unflagged(errors: list[str], output: ExtractionOutput | None, message: str) -> bool:
    """Chybná hodnota, kterou aplikace uživateli neoznačila jako odhad AI (pravidlo 8)."""
    if output is None or not errors:
        return False
    proposal = proposal_from_extraction(output, None, message)
    return not proposal.estimated


def rate_limited(record: CaseRecord) -> bool:
    """Případ bez odpovědi kvůli limitu poskytovatele (neříká nic o kvalitě modelu)."""
    return bool(record.calls) and all(
        (call.error or "").startswith("rate_limit") for call in record.calls
    )


def _key(pair: tuple[int | None, int | None]) -> tuple[int, int]:
    return (pair[0] or -1, pair[1] or -1)


def _stock_key(pair: tuple[int | None, Decimal | None]) -> tuple[int, Decimal]:
    return (pair[0] or -1, pair[1] if pair[1] is not None else Decimal(-1))


def objective_ok(expected: dict[str, Any], output: ExtractionOutput | None) -> bool:
    got = output.objective.value if output and output.objective else None
    return output is not None and expected["objective"] == got


def _money(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def cost_usd(model: str, record: CaseRecord) -> Decimal:
    price_in, price_out = PRICES_USD_PER_MTOK.get(model, (Decimal(0), Decimal(0)))
    tokens_in = sum(c.prompt_tokens for c in record.calls)
    tokens_out = sum(c.completion_tokens for c in record.calls)
    return (tokens_in * price_in + tokens_out * price_out) / Decimal(1_000_000)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, round(0.95 * len(ordered)) - 1)]


def _record(data: dict[str, Any]) -> CaseRecord:
    calls = [CallRecord(**call) for call in data["calls"]]
    return CaseRecord(
        case_id=data["case_id"],
        model=data["model"],
        latency_s=data["latency_s"],
        calls=calls,
        prompt_version=data["prompt_version"],
        prompt_source=data["prompt_source"],
    )


def summarize(raw: dict[str, Any]) -> str:
    cases = {case["id"]: case for case in raw["cases"]}
    lines = [
        f"Běh `{raw['run_id']}`, {raw['date']}, sada `{raw['set']}` ({len(cases)} případů), "
        f"formát `{raw['response_format']}`, schéma `{raw['schema_version']}`. "
        "„Platné“ jsou počítané z případů, které dostaly odpověď (bez `api_rate_limit`).",
        "",
        "| Model | Prompt | Úplná shoda (95% interval) | Platné bez opravy | Platné celkem | Cíl | "
        "Vymyšlená hodnota | Neoznačená chyba | "
        "Latence medián / p95 | Čas modelu medián | Tokeny vstup / výstup (reasoning) | "
        "Cena za běh |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    failures: list[str] = []
    categories: dict[str, Counter[str]] = {}
    correct_by_model: dict[str, dict[str, bool]] = {}
    for model, model_records in raw["results"].items():
        records = [_record(r) for r in model_records]
        n = len(records)
        exact = 0
        first_valid = 0
        any_valid = 0
        objective = 0
        answered = 0
        invented = 0
        silent = 0
        counter: Counter[str] = Counter()
        for record in records:
            case = cases[record.case_id]
            output = final_output(record)
            errors = compare(case["expected"], record)
            answered += not rate_limited(record)
            counter.update(errors)
            exact += not errors
            first_valid += bool(record.calls and record.calls[0].schema_valid)
            any_valid += output is not None
            objective += objective_ok(case["expected"], output)
            invented += hallucinated(case["expected"], output)
            silent += unflagged(errors, output, case["input"])
            correct_by_model.setdefault(model, {})[record.case_id] = not errors
            if errors:
                got = (
                    output.model_dump(
                        mode="json",
                        include={"parts", "stock", "kerf_mm", "trim_mm", "min_remnant_mm"},
                    )
                    if output
                    else [c.error for c in record.calls]
                )
                detail = json.dumps(got, ensure_ascii=False)
                failures.append(f"- `{model}` `{record.case_id}` ({', '.join(errors)}): `{detail}`")
        categories[model] = counter
        latencies = [r.latency_s for r in records]
        model_times = [c.model_time_s for r in records for c in r.calls if c.model_time_s]
        model_time = f"{statistics.median(model_times):.2f} s" if model_times else "–"
        tokens_in = sum(c.prompt_tokens for r in records for c in r.calls)
        tokens_out = sum(c.completion_tokens for r in records for c in r.calls)
        reasoning = sum(c.reasoning_tokens for r in records for c in r.calls)
        cost = sum((cost_usd(model, r) for r in records), Decimal(0))
        versions = {(r.prompt_source, r.prompt_version) for r in records}
        prompt = ", ".join(f"{s} v{v}" for s, v in sorted(versions, key=str))
        lines.append(
            f"| `{model}` | {prompt} | {interval(exact, n)} | {first_valid}/{answered} | "
            f"{any_valid}/{answered} | {objective}/{n} | {invented}/{n} | {silent}/{n} | "
            f"{statistics.median(latencies):.2f} / "
            f"{_p95(latencies):.2f} s | {model_time} | {tokens_in} / {tokens_out} ({reasoning}) | "
            f"{cost:.4f} USD |"
        )
    lines += ["", *paired(correct_by_model)]
    lines += ["", "Chyby podle kategorií (počet případů):", ""]
    all_categories = sorted({c for counter in categories.values() for c in counter})
    lines.append("| Kategorie | " + " | ".join(f"`{m}`" for m in categories) + " |")
    lines.append("|---" * (len(categories) + 1) + "|")
    for category in all_categories:
        counts = " | ".join(str(categories[m][category]) for m in categories)
        lines.append(f"| `{category}` | {counts} |")
    lines += ["", "Chybné případy:", "", *failures]
    return "\n".join(lines)


def paired(correct: dict[str, dict[str, bool]]) -> list[str]:
    """Párové srovnání modelů na stejných případech (přesný McNemarův test)."""
    models = list(correct)
    lines = ["Párové srovnání (McNemar, stejné případy):", ""]
    for index, a in enumerate(models):
        for b in models[index + 1 :]:
            shared = correct[a].keys() & correct[b].keys()
            only_a = sum(correct[a][c] and not correct[b][c] for c in shared)
            only_b = sum(correct[b][c] and not correct[a][c] for c in shared)
            p = mcnemar(only_a, only_b)
            lines.append(f"- `{a}` × `{b}`: jen první {only_a}, jen druhý {only_b}, p = {p:.2f}")
    return lines if len(models) > 1 else []


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text("utf-8")))


def merge_raw(raws: list[dict[str, Any]]) -> dict[str, Any]:
    """Sloučí běhy: záznam (model, případ) z pozdějšího běhu nahradí dřívější."""
    merged = dict(raws[0])
    results: dict[str, dict[str, Any]] = {
        model: {r["case_id"]: r for r in records} for model, records in raws[0]["results"].items()
    }
    for raw in raws[1:]:
        for model, records in raw["results"].items():
            results.setdefault(model, {}).update({r["case_id"]: r for r in records})
    merged["run_id"] = " + ".join(raw["run_id"] for raw in raws)
    merged["results"] = {model: list(records.values()) for model, records in results.items()}
    return merged


# --- Vstupní bod -------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else None)
    parser.add_argument("--set", default="dev", choices=("dev", "test"))
    parser.add_argument("--models", default=None)
    parser.add_argument("--format", default="json_object", choices=("json_object", "json_schema"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--cases", default=None, help="jen vybrané případy (id oddělená čárkou)")
    parser.add_argument("--pause", type=float, default=0.0, help="pauza mezi případy v s")
    parser.add_argument(
        "--from-raw", type=Path, nargs="+", default=None, help="pozdější soubory přepíšou dřívější"
    )
    args = parser.parse_args()

    if args.from_raw is not None:
        print(summarize(merge_raw([_load(path) for path in args.from_raw])))
        return

    models = (
        tuple(args.models.split(","))
        if args.models
        else ((os.environ["LLM_MODEL"],) if os.environ.get("LLM_MODEL") else DEFAULT_MODELS)
    )
    cases = load_cases(args.set)
    if args.cases:
        cases = [case for case in cases if case["id"] in args.cases.split(",")]
    cases = cases[: args.limit]
    now = datetime.now(UTC)
    run_id = f"{now:%Y%m%d-%H%M}-{uuid.uuid4().hex[:4]}"
    results = {
        model: [asdict(r) for r in run_model(model, cases, run_id, args.format, args.pause)]
        for model in models
    }
    raw: dict[str, Any] = {
        "run_id": run_id,
        "date": now.isoformat(timespec="seconds"),
        "set": args.set,
        "response_format": args.format,
        "schema_version": SCHEMA_VERSION,
        "cases": cases,
        "results": results,
    }
    out = REPORTS_DIR / "raw" / f"{now:%Y-%m-%d}-extraction-{args.set}-{args.format}-{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"Surové výsledky: {out.relative_to(ROOT)}\n")
    print(summarize(raw))


if __name__ == "__main__":
    main()
