"""`JevRouter`: rozpoznání úlohy přes TypeSafe Jev (System One, ADR-0004, ADR-0012).

Otázky a rozhodovací tabulky jsou v `jev_questions.py`. Chyba API je chyba routeru
(záloha přepne na další implementaci), nikdy „unclear“. Klíč se čte jen tady
a nikam se nezapisuje.
"""

from typing import Any, cast

from typesafe_sdk import RetryPolicy, TypeSafeClient, TypeSafeError

from decision_engine.adapters.jev_questions import DEFAULT_VARIANT, MODEL, VARIANTS
from decision_engine.app.ports import RoutingError, RoutingRequest
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.routing import RouteOutcome, RoutingDecision

TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 1


class JevRouter:
    """`Router` nad TypeSafe Jev."""

    name = "jev"

    def __init__(self, client: TypeSafeClient, variant: str = DEFAULT_VARIANT) -> None:
        self._client = client
        self._variant = VARIANTS.get(variant, VARIANTS[DEFAULT_VARIANT])

    @classmethod
    def create(cls, api_key: str, variant: str = DEFAULT_VARIANT) -> "JevRouter":
        client = TypeSafeClient(
            api_key=api_key,
            model=MODEL,
            retry=RetryPolicy(max_retries=MAX_RETRIES),
            timeout=TIMEOUT_SECONDS,
        )
        return cls(client, variant)

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]:
        order = request.order.get("rozpracovana_zakazka")
        has_order = isinstance(order, dict)
        questions = self._variant.questions()
        if not has_order:
            questions.pop("intent", None)
        state = {"zprava": request.message, **request.order}
        try:
            # Typ `state` v SDK obsahuje rekurzivní alias, který pyright neumí plně odvodit.
            response = self._client.system_one(  # pyright: ignore[reportUnknownMemberType]
                state=cast(Any, state), questions=questions
            )
        except TypeSafeError as error:
            return Err(RoutingError(router=self.name, detail=type(error).__name__))
        answers = {key: answer.model_dump(mode="json") for key, answer in response.answers.items()}
        capability, intent = self._variant.decide(answers, has_order)
        return Ok(_decision(capability, intent))


def _decision(capability: str, intent: str | None) -> RoutingDecision:
    match capability:
        case "unclear":
            return RoutingDecision(outcome=RouteOutcome.UNCLEAR, router="jev")
        case "cutting_1d" | "cost_estimate":
            return RoutingDecision.model_validate(
                {
                    "outcome": RouteOutcome.SUPPORTED,
                    "capability": capability,
                    "intent": intent,
                    "router": "jev",
                }
            )
        case _:
            return RoutingDecision(outcome=RouteOutcome.UNSUPPORTED, router="jev")
