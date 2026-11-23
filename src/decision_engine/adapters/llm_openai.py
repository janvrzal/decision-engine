"""Generativní model přes OpenAI-kompatibilní API (ADR-0008): Groq, OpenAI, Ollama …

S Langfuse se použije klient z `langfuse.openai`, který každé volání zaznamená jako
`generation` s propojeným promptem. Bez Langfuse obyčejný klient `openai`.
"""

import importlib
from collections.abc import Sequence
from typing import Any, cast

import openai
from langfuse import get_client

from decision_engine.app.ports import ChatMessage, LlmError, Prompt
from decision_engine.core.result import Err, Ok, Result

GENERATION_NAME = "extract-proposal"
MAX_RETRIES = 2
"""Omezené opakování dočasných chyb (spec kap. 8); SDK respektuje `retry-after`."""
TIMEOUT_SECONDS = 30.0


class OpenAICompatibleLlm:
    """`LlmClient` nad SDK `openai` s volitelným trasováním Langfuse."""

    def __init__(self, client: Any, model: str, *, traced: bool) -> None:
        self._client = client
        self._model = model
        self._traced = traced

    @classmethod
    def create(
        cls, *, base_url: str, api_key: str, model: str, traced: bool, http_client: Any = None
    ) -> "OpenAICompatibleLlm":
        if traced:
            # Import až zde: modul langfuse.openai obaluje SDK openai, bez Langfuse ho nechceme.
            # (Dokumentované API `from langfuse.openai import OpenAI`; modul ho neexportuje
            # pro typovou kontrolu, proto import_module.)
            client_class: Any = importlib.import_module("langfuse.openai").OpenAI
        else:
            client_class = openai.OpenAI
        client = client_class(
            base_url=base_url,
            api_key=api_key,
            max_retries=MAX_RETRIES,
            timeout=TIMEOUT_SECONDS,
            http_client=http_client,
        )
        return cls(client, model, traced=traced)

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        tracing: dict[str, Any] = {}
        if self._traced:
            tracing = {
                "name": GENERATION_NAME,
                "metadata": {"attempt": attempt, "prompt_source": prompt.source},
            }
            if prompt.handle is not None:
                tracing["langfuse_prompt"] = prompt.handle
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[message.model_dump() for message in messages],
                response_format={"type": "json_object"},
                temperature=0,
                **tracing,
            )
        except openai.RateLimitError as error:
            return Err(LlmError(kind="rate_limit", detail=str(error)))
        except (openai.APIConnectionError, openai.APITimeoutError) as error:
            return Err(LlmError(kind="connection", detail=str(error)))
        except openai.AuthenticationError as error:
            return Err(LlmError(kind="connection", detail=f"neplatný klíč: {error}"))
        except openai.APIStatusError as error:
            # Např. Groq `json_validate_failed`: model nevrátil platný JSON.
            return Err(LlmError(kind="invalid_response", detail=str(error)))

        message = response.choices[0].message if response.choices else None
        if self._traced and message is not None:
            _record_reasoning(message, attempt)
        content = message.content if message is not None else None
        if not content:
            return Err(LlmError(kind="invalid_response", detail="prázdná odpověď modelu"))
        return Ok(str(content))


def _record_reasoning(message: Any, attempt: int) -> None:
    """Uloží úvahu modelu (thinking) do trace kola.

    Integrace `langfuse.openai` ukládá z odpovědi jen `content`; pole `reasoning`, které
    Groq vrací u modelů s uvažováním, by se ztratilo. Best practices Langfuse ho chtějí
    zachytit, proto ho připíšeme do metadat právě aktivní observation (kořen kola).
    """
    extra = cast(dict[str, object], message.model_extra or {})
    reasoning = extra.get("reasoning")
    if not reasoning:
        return
    get_client().update_current_span(metadata={f"reasoning_attempt_{attempt}": reasoning})
