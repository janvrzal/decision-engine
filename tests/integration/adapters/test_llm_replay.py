"""Přehrávaný model pro end-to-end testy UI."""

import json
from pathlib import Path

import pytest

from decision_engine.adapters.config import build_ai_adapters
from decision_engine.adapters.llm_replay import ReplayLlm
from decision_engine.app.ports import ChatMessage, LlmError, Prompt
from decision_engine.core.result import Err, Ok, Result

pytestmark = pytest.mark.integration

FIXTURE = Path(__file__).resolve().parents[3] / "frontend" / "e2e" / "fixtures" / "uc01.json"
PROMPT = Prompt(name="extract-proposal-1d", version=None, source="fallback", messages=())


def _ask(llm: ReplayLlm, text: str) -> Result[str, LlmError]:
    messages = [
        ChatMessage(role="system", content="regál v systému"),
        ChatMessage(role="user", content=text),
    ]
    return llm.complete_json(messages, prompt=PROMPT, attempt=1)


def test_odpoved_podle_zpravy_uzivatele() -> None:
    match _ask(ReplayLlm.from_file(FIXTURE), "Potřebuji REGÁL"):
        case Ok(text):
            assert json.loads(text)["parts"][0]["name"] == "noha"
        case other:
            pytest.fail(str(other))


def test_prehrana_chyba() -> None:
    result = _ask(ReplayLlm.from_file(FIXTURE), "simuluj výpadek")

    assert isinstance(result, Err)
    assert result.error.kind == "connection"


def test_bez_shody_je_neplatna_odpoved() -> None:
    result = _ask(ReplayLlm.from_file(FIXTURE), "něco jiného")

    assert isinstance(result, Err)
    assert result.error.kind == "invalid_response"


def test_konfigurace_pouzije_prehravani() -> None:
    adapters = build_ai_adapters({"LLM_REPLAY_FILE": str(FIXTURE)})

    assert isinstance(adapters.llm, ReplayLlm)


def test_odpoved_routeru_se_vybere_podle_nazvu_promptu() -> None:
    llm = ReplayLlm(
        [
            {"match": "skříň", "response": {"name": "extrakce"}},
            {"match": "skříň", "prompt": "route-request", "response": {"capability": "unclear"}},
        ]
    )
    route = Prompt(name="route-request", version=None, source="fallback", messages=())
    message = [ChatMessage(role="user", content="Chci skříň.")]

    assert llm.complete_json(message, prompt=route, attempt=1) == Ok('{"capability": "unclear"}')
    assert llm.complete_json(message, prompt=PROMPT, attempt=1) == Ok('{"name": "extrakce"}')
