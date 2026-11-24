"""`LlmRouter`: rozpoznání úlohy generativním modelem (ADR-0012).

Výstup je omezený na stejnou množinu možností jako u Jev a validuje se schématem.
U nejasného zadání model napíše jednu doptávací otázku. Neplatná odpověď nebo výpadek
je chyba routeru (záloha přepne dál), nikdy „unclear“.
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from decision_engine.app.ports import LlmClient, PromptStore, RoutingError, RoutingRequest
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.routing import RouteOutcome, RoutingDecision

ROUTE_PROMPT = "route-request"
MAX_QUESTION_CHARS = 300


class RouteOutput(BaseModel):
    """Co má model vrátit."""

    model_config = ConfigDict(extra="ignore")

    capability: Literal["cutting_1d", "cost_estimate", "unclear", "unsupported"]
    intent: Literal["new_order", "change_order", "result_question"] | None = None
    question: str | None = Field(None, max_length=MAX_QUESTION_CHARS)


_SCHEMA = json.dumps(RouteOutput.model_json_schema(), ensure_ascii=False)


class LlmRouter:
    """`Router` nad `LlmClient` s promptem `route-request` ze správy promptů."""

    name = "llm"

    def __init__(self, llm: LlmClient, prompts: PromptStore) -> None:
        self._llm = llm
        self._prompts = prompts

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]:
        order = json.dumps(request.order, ensure_ascii=False, indent=2)
        prompt = self._prompts.get(
            ROUTE_PROMPT, {"schema": _SCHEMA, "order": order, "message": request.message}
        )
        match self._llm.complete_json(prompt.messages, prompt=prompt, attempt=1):
            case Err(error):
                return Err(RoutingError(router=self.name, detail=f"{error.kind}: {error.detail}"))
            case Ok(text):
                try:
                    output = RouteOutput.model_validate_json(text)
                except ValidationError as error:
                    detail = f"neplatná odpověď: {error.error_count()} chyb"
                    return Err(RoutingError(router=self.name, detail=detail))
        has_order = isinstance(request.order.get("rozpracovana_zakazka"), dict)
        return Ok(_decision(output, has_order=has_order))


def _decision(output: RouteOutput, *, has_order: bool) -> RoutingDecision:
    intent = (output.intent or "new_order") if has_order else "new_order"
    match output.capability:
        case "unclear":
            question = (output.question or "").strip() or None
            return RoutingDecision(
                outcome=RouteOutcome.UNCLEAR, intent=intent, question=question, router="llm"
            )
        case "unsupported":
            return RoutingDecision(outcome=RouteOutcome.UNSUPPORTED, router="llm")
        case capability:
            return RoutingDecision(
                outcome=RouteOutcome.SUPPORTED, capability=capability, intent=intent, router="llm"
            )
