"""Přehrávaný model: připravené odpovědi ze souboru místo volání AI.

Slouží end-to-end testům UI (deterministický běh bez sítě a klíčů) a později demu
(service design F6). Odpověď se vybere podle textu poslední zprávy uživatele a názvu
promptu (`prompt`, výchozí je extrakce; router má vlastní odpovědi):

    {"answers": [
        {"match": "regál", "response": {...výstup extrakce...}},
        {"match": "skříň", "prompt": "route-request", "response": {"capability": "unclear"}},
        {"match": "výpadek", "error": "connection"}
    ]}
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from decision_engine.app.ports import ChatMessage, LlmError, Prompt
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.state import AiErrorKind

_ERROR_KINDS: tuple[AiErrorKind, ...] = ("connection", "rate_limit", "invalid_response")
DEFAULT_PROMPT = "extract-proposal-1d"
"""Odpovědi bez `prompt` patří extrakci (i jejímu opravnému pokusu)."""


class ReplayLlm:
    """`LlmClient`, který vrací odpovědi podle shody s textem zprávy uživatele."""

    def __init__(self, answers: Sequence[dict[str, Any]]) -> None:
        self._answers = tuple(answers)

    @classmethod
    def from_file(cls, path: Path) -> "ReplayLlm":
        data = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        return cls(cast(list[dict[str, Any]], data["answers"]))

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        user_text = next((m.content for m in reversed(messages) if m.role == "user"), "").lower()
        for answer in self._answers:
            if str(answer.get("prompt", DEFAULT_PROMPT)) != prompt.name:
                continue
            if str(answer.get("match", "")).lower() in user_text:
                error = answer.get("error")
                for kind in _ERROR_KINDS:
                    if kind == error:
                        return Err(LlmError(kind=kind, detail="přehraná chyba"))
                return Ok(json.dumps(answer["response"], ensure_ascii=False))
        return Err(LlmError(kind="invalid_response", detail="žádná přehraná odpověď"))
