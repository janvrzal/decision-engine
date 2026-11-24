"""Adaptéry AI bez sítě: OpenAI-kompatibilní klient nad nahranou odpovědí, prompty, konfigurace."""

import json
from pathlib import Path
from typing import Any

import httpx
import httpx2
import openai
import pytest

from decision_engine.adapters.config import UnavailableLlm, build_ai_adapters
from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.adapters.langfuse_prompts import LangfusePromptStore
from decision_engine.adapters.llm_openai import OpenAICompatibleLlm
from decision_engine.adapters.noop_tracing import NoopTracer
from decision_engine.app.ports import ChatMessage, Prompt
from decision_engine.core.result import Err, Ok

pytestmark = pytest.mark.integration

PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"
PROMPT = Prompt(name="test", version=None, source="fallback", messages=())
MESSAGES = [ChatMessage(role="user", content="Odpověz JSON.")]

# Zkrácená skutečná odpověď Groq chat completions.
GROQ_RESPONSE: dict[str, Any] = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1_763_900_000,
    "model": "test-model",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": '{"parts": []}'},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 120, "completion_tokens": 8, "total_tokens": 128},
}


def _llm(status: int, body: dict[str, Any]) -> tuple[OpenAICompatibleLlm, list[httpx2.Request]]:
    requests: list[httpx2.Request] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(status, json=body)

    client = openai.OpenAI(
        base_url="https://api.groq.test/openai/v1",
        api_key="test",
        max_retries=0,
        # SDK openai 3.x stojí na httpx2.
        http_client=httpx2.Client(transport=httpx2.MockTransport(respond)),
    )
    return OpenAICompatibleLlm(client, "test-model", traced=False), requests


def test_odpoved_modelu_vrati_text_a_posle_json_mode() -> None:
    llm, requests = _llm(200, GROQ_RESPONSE)

    result = llm.complete_json(MESSAGES, prompt=PROMPT, attempt=1)

    assert result == Ok('{"parts": []}')
    sent = json.loads(requests[0].content)
    assert sent["model"] == "test-model"
    assert sent["response_format"] == {"type": "json_object"}
    assert sent["messages"] == [{"role": "user", "content": "Odpověz JSON."}]
    assert "name" not in sent  # bez Langfuse žádné parametry navíc


@pytest.mark.parametrize(
    ("status", "kind"),
    [
        (429, "rate_limit"),
        (400, "invalid_response"),
        (500, "connection"),  # výpadek poskytovatele, ne vadná odpověď
        (401, "configuration"),  # neplatný klíč: opakování nepomůže
    ],
)
def test_chyby_api_se_prevedou_na_druh_chyby(status: int, kind: str) -> None:
    llm, _ = _llm(status, {"error": {"message": "chyba"}})

    match llm.complete_json(MESSAGES, prompt=PROMPT, attempt=1):
        case Err(error):
            assert error.kind == kind
        case Ok(text):
            pytest.fail(f"čekal jsem chybu, přišlo {text}")


def test_prazdna_odpoved_je_neplatna() -> None:
    empty = {"index": 0, "message": {"role": "assistant", "content": ""}, "finish_reason": "stop"}
    body = {**GROQ_RESPONSE, "choices": [empty]}
    llm, _ = _llm(200, body)

    result = llm.complete_json(MESSAGES, prompt=PROMPT, attempt=1)

    assert isinstance(result, Err)


def test_bez_promennych_prostredi_bezi_bez_ai_i_langfuse() -> None:
    adapters = build_ai_adapters({}, PROMPTS_DIR)

    assert isinstance(adapters.tracer, NoopTracer)
    assert isinstance(adapters.prompts, FilePromptStore)
    assert isinstance(adapters.llm, UnavailableLlm)
    assert not adapters.langfuse_enabled
    result = adapters.llm.complete_json(MESSAGES, prompt=PROMPT, attempt=1)
    assert isinstance(result, Err)


def test_zalozni_prompt_dosadi_promenne() -> None:
    prompt = FilePromptStore(PROMPTS_DIR).get(
        "extract-proposal-1d", {"schema": "{}", "base_project": "žádná", "message": "4 nohy"}
    )

    assert prompt.source == "fallback"
    user = prompt.messages[-1]
    assert user.role == "user"
    assert user.content.endswith("Zpráva uživatele:\n4 nohy")
    assert "<zakazka>\nžádná\n</zakazka>" in user.content
    assert "JSON" in prompt.messages[0].content  # Groq json_object vyžaduje slovo JSON
    assert "{{" not in prompt.messages[0].content


def test_textovy_prompt_je_jedna_zprava_uzivatele() -> None:
    prompt = FilePromptStore(PROMPTS_DIR).get("repair-invalid-json", {"errors": "parts: chybí"})

    (message,) = prompt.messages
    assert message.role == "user"
    assert "parts: chybí" in message.content


class _FailingLangfuse:
    def get_prompt(self, *args: object, **kwargs: object) -> object:
        raise httpx.ConnectError("Langfuse nedostupný")


def test_nedostupny_langfuse_pouzije_zalozni_prompt() -> None:
    fallback = FilePromptStore(PROMPTS_DIR)
    store = LangfusePromptStore(_FailingLangfuse(), fallback)  # type: ignore[arg-type]

    prompt = store.get("repair-invalid-json", {"errors": "x"})

    assert prompt.source == "fallback"
    assert prompt.handle is None
