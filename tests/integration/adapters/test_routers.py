"""Adaptéry routeru bez sítě (ADR-0012): LLM router, rozhodovací tabulky Jev, konfigurace."""

import json
from collections.abc import Sequence
from typing import Any

import pytest

from decision_engine.adapters.config import PROMPTS_DIR, UnavailableLlm, build_router
from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.adapters.jev_questions import decide_decomposed, decide_naive
from decision_engine.adapters.llm_replay import ReplayLlm
from decision_engine.adapters.llm_router import LlmRouter
from decision_engine.app.ports import ChatMessage, LlmError, ManualRouter, Prompt, RoutingRequest
from decision_engine.app.routing import FallbackRouter
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.routing import NO_ORDER, RouteOutcome

PROMPTS = FilePromptStore(PROMPTS_DIR)
NEW = RoutingRequest(message="Chci skříň.", order={"rozpracovana_zakazka": NO_ORDER})


class _Llm:
    def __init__(self, reply: Result[str, LlmError]) -> None:
        self.reply = reply
        self.prompts: list[str] = []

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        self.prompts.append(prompt.name)
        return self.reply


def test_llm_router_doptani_s_otazkou() -> None:
    reply = json.dumps({"capability": "unclear", "question": "Z čeho bude skříň?"})
    llm = _Llm(Ok(reply))

    result = LlmRouter(llm, PROMPTS).route(NEW)

    assert llm.prompts == ["route-request"]
    match result:
        case Ok(decision):
            assert decision.outcome is RouteOutcome.UNCLEAR
            assert decision.question == "Z čeho bude skříň?"
            assert decision.router == "llm"
        case Err():
            pytest.fail("router měl rozhodnout")


def test_llm_router_bez_zakazky_je_zamer_vzdy_nova_zakazka() -> None:
    llm = _Llm(Ok(json.dumps({"capability": "cutting_1d", "intent": "change_order"})))

    match LlmRouter(llm, PROMPTS).route(NEW):
        case Ok(decision):
            assert decision.intent == "new_order"
        case Err():
            pytest.fail("router měl rozhodnout")


@pytest.mark.parametrize(
    "reply",
    [Ok("nesmysl"), Ok('{"capability": "letadlo"}'), Err(LlmError("connection", "x"))],
)
def test_llm_router_chyba_neni_nejasne_zadani(reply: Result[str, LlmError]) -> None:
    assert isinstance(LlmRouter(_Llm(reply), PROMPTS).route(NEW), Err)


def test_prompt_routeru_vklada_zakazku_jako_ohranicena_data() -> None:
    prompt = PROMPTS.get("route-request", {"schema": "{}", "order": "ZAKAZKA", "message": "M"})

    system = prompt.messages[0].content
    assert "<zakazka>\nZAKAZKA\n</zakazka>" in system
    assert prompt.messages[-1].role == "user"
    assert prompt.messages[-1].content == "M"


def _choice(choice: str, probability: float) -> dict[str, Any]:
    return {"choice": choice, "probabilities": {choice: probability}}


def test_jev_jednoducha_varianta_pod_prahem_je_nejasne() -> None:
    answers = {"capability": _choice("cutting_1d", 0.6)}

    assert decide_naive(answers, has_order=False) == ("unclear", "new_order")


@pytest.mark.parametrize(
    ("task", "concrete", "expected"),
    [
        ("cutting_bars", 0.9, "cutting_1d"),
        ("cutting_bars", 0.1, "unclear"),
        ("pricing", 0.1, "cost_estimate"),
        ("packing", 0.9, "unsupported"),
        ("other_request", 0.5, "unclear"),
        ("other_request", 0.9, "unsupported"),
    ],
)
def test_jev_pravdivostni_tabulka(task: str, concrete: float, expected: str) -> None:
    answers = {"task": _choice(task, 0.95), "concrete": {"noul": concrete}}

    assert decide_decomposed(answers, has_order=False)[0] == expected


def test_bez_klicu_je_router_rucni() -> None:
    router = build_router({}, UnavailableLlm(), PROMPTS)

    assert router.name == "manual"


def test_s_modelem_je_vychozi_llm_a_rucni_volba_prepise() -> None:
    llm = ReplayLlm([])

    assert isinstance(build_router({}, llm, PROMPTS), FallbackRouter)
    assert build_router({}, llm, PROMPTS).name == "llm"
    assert isinstance(build_router({"ROUTER": "manual"}, llm, PROMPTS), ManualRouter)
