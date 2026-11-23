"""Vykonání efektu `CallExtractor`: zpráva → návrh změny přes generativní model (ADR-0008).

Výstup modelu se vždy validuje schématem. Při neplatném výstupu proběhne nejvýše jeden
opravný pokus s chybami validace; potom `AiFailed`. Texty promptů jsou v Langfuse
(záloha v `prompts/`), ne v kódu.
"""

import json
from dataclasses import dataclass

from pydantic import ValidationError

from decision_engine.app.ports import ChatMessage, Ports, Prompt
from decision_engine.core.effects import CallExtractor
from decision_engine.core.events import AiFailed, Event, ProposalReceived
from decision_engine.core.extraction import ExtractionOutput, proposal_from_extraction
from decision_engine.core.result import Err, Ok

EXTRACT_PROMPT = "extract-proposal-1d"
REPAIR_PROMPT = "repair-invalid-json"
MAX_ATTEMPTS = 2
"""První pokus a jeden opravný (ADR-0008)."""

_SCHEMA = json.dumps(ExtractionOutput.model_json_schema(), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class ExtractionTrace:
    """Co se o extrakci zapíše do trasování (bez tajných údajů)."""

    prompt_name: str
    prompt_version: int | None
    prompt_source: str
    attempts: int
    validation_errors: tuple[str, ...]


def run_extraction(effect: CallExtractor, ports: Ports) -> tuple[Event, ExtractionTrace]:
    """Zavolá model, ověří výstup a vrátí výslednou událost a údaje pro trasování."""
    base = effect.base.model_dump_json(indent=2) if effect.base else "žádná (nová zakázka)"
    prompt = ports.prompts.get(
        EXTRACT_PROMPT, {"schema": _SCHEMA, "base_project": base, "message": effect.text}
    )
    messages = list(prompt.messages)
    errors: tuple[str, ...] = ()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        match ports.llm.complete_json(messages, prompt=prompt, attempt=attempt):
            case Err(error):
                return AiFailed(kind=error.kind), _trace(prompt, attempt, errors)
            case Ok(text):
                try:
                    output = ExtractionOutput.model_validate_json(text)
                except ValidationError as error:
                    errors = tuple(_describe(error))
                    messages += [
                        ChatMessage(role="assistant", content=text),
                        *_repair_messages(ports, errors),
                    ]
                    continue
                proposal = proposal_from_extraction(output, effect.base)
                event = ProposalReceived(proposal=proposal, reply=output.reply)
                return event, _trace(prompt, attempt, errors)

    return AiFailed(kind="invalid_response"), _trace(prompt, MAX_ATTEMPTS, errors)


def _repair_messages(ports: Ports, errors: tuple[str, ...]) -> tuple[ChatMessage, ...]:
    repair = ports.prompts.get(REPAIR_PROMPT, {"errors": "\n".join(errors)})
    return repair.messages


def _describe(error: ValidationError) -> list[str]:
    return [
        f"{'.'.join(str(part) for part in detail['loc']) or '(celý výstup)'}: {detail['msg']}"
        for detail in error.errors()
    ]


def _trace(prompt: Prompt, attempts: int, errors: tuple[str, ...]) -> ExtractionTrace:
    return ExtractionTrace(
        prompt_name=prompt.name,
        prompt_version=prompt.version,
        prompt_source=prompt.source,
        attempts=attempts,
        validation_errors=errors,
    )
