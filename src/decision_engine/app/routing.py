"""Řetěz routerů se zálohou (ADR-0012): chyba API se nikdy nevykládá jako „unclear“.

První router, který rozhodne, vyhrává; selže-li, zkusí se další a důvod se zapíše
do rozhodnutí (`fallback_reason`). Poslední v řetězu je vždy `ManualRouter`.
"""

from collections.abc import Sequence

from decision_engine.app.ports import ManualRouter, Router, RoutingError, RoutingRequest
from decision_engine.core.result import Err, Ok, Result
from decision_engine.core.routing import RoutingDecision


class FallbackRouter:
    """`Router`, který zkouší implementace v pořadí, dokud některá nerozhodne."""

    def __init__(self, routers: Sequence[Router]) -> None:
        chain = [router for router in routers if not isinstance(router, ManualRouter)]
        self._routers: tuple[Router, ...] = (*chain, ManualRouter())
        self.name = self._routers[0].name

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]:
        failures: list[str] = []
        for router in self._routers:
            match router.route(request):
                case Ok(decision):
                    if not failures:
                        return Ok(decision)
                    reason = "; ".join(failures)
                    return Ok(decision.model_copy(update={"fallback_reason": reason}))
                case Err(error):
                    failures.append(f"{error.router}: {error.detail}")
        # Nedosažitelné: `ManualRouter` vždy rozhodne.
        return Err(RoutingError(router=self.name, detail="; ".join(failures)))
