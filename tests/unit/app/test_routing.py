"""Řetěz routerů se zálohou (ADR-0012): chyba API přepne na další implementaci."""

from decision_engine.app.ports import ManualRouter, RoutingError, RoutingRequest
from decision_engine.app.routing import FallbackRouter
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.routing import RouteOutcome, RoutingDecision

REQUEST = RoutingRequest(message="Chci skříň.", order={})


class _Failing:
    name = "jev"

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]:
        return Err(RoutingError(router=self.name, detail="výpadek"))


class _Unclear:
    name = "llm"

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]:
        return Ok(RoutingDecision(outcome=RouteOutcome.UNCLEAR, router=self.name))


def test_prvni_router_ktery_rozhodne_vyhrava() -> None:
    match FallbackRouter([_Unclear()]).route(REQUEST):
        case Ok(decision):
            assert decision.router == "llm"
            assert decision.fallback_reason is None
        case Err():
            raise AssertionError("router měl rozhodnout")


def test_vypadek_neni_nejasne_zadani_a_prepne_na_dalsi() -> None:
    match FallbackRouter([_Failing(), _Unclear()]).route(REQUEST):
        case Ok(decision):
            assert decision.router == "llm"
            assert decision.fallback_reason == "jev: výpadek"
        case Err():
            raise AssertionError("záloha měla rozhodnout")


def test_posledni_zaloha_je_rucni_router() -> None:
    match FallbackRouter([_Failing()]).route(REQUEST):
        case Ok(decision):
            assert decision.router == ManualRouter.name
            assert decision.outcome is RouteOutcome.SUPPORTED
        case Err():
            raise AssertionError("ruční router vždy rozhodne")
