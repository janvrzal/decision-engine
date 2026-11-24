"""Porty aplikační vrstvy: co `app/` potřebuje od okolí (ADR-0006, ADR-0008, ADR-0009).

Implementace jsou v `adapters/`. `app/` zná jen tato rozhraní, takže běží i s falešnými
adaptéry bez sítě, klíčů a Langfuse (AGENTS.md pravidlo 11).
"""

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.result import Ok, Result
from decision_engine.core.routing import RouteOutcome, RoutingDecision
from decision_engine.core.state import AiErrorKind


class ChatMessage(BaseModel):
    """Zpráva pro generativní model ve formátu OpenAI."""

    model_config = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class Prompt:
    """Prompt připravený k odeslání: zprávy s dosazenými proměnnými a jeho původ."""

    name: str
    version: int | None
    source: Literal["langfuse", "fallback"]
    messages: tuple[ChatMessage, ...]
    handle: object = None
    """Neprůhledný odkaz pro adaptér (propojení promptu s trace); `app/` ho nečte."""


class PromptStore(Protocol):
    """Prompty podle názvu (Langfuse se štítkem `production`, nebo záloha z `prompts/`)."""

    def get(self, name: str, variables: Mapping[str, str]) -> Prompt: ...


@dataclass(frozen=True, slots=True)
class LlmError:
    """Selhání volání modelu s druhem chyby pro UI."""

    kind: AiErrorKind
    detail: str


class LlmClient(Protocol):
    """Generativní model se strukturovaným výstupem (ADR-0008)."""

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        """Vrátí text odpovědi, který má být JSON; validaci schématem dělá volající."""
        ...


class Turn(Protocol):
    """Jedno kolo zpracování v trasování (jeden trace)."""

    def set_output(self, output: object) -> None: ...

    def set_metadata(self, metadata: Mapping[str, object]) -> None: ...

    def fail(self, message: str) -> None: ...


class Tracer(Protocol):
    """Trasování kol dialogu (Langfuse), nebo nic, když není nastavené."""

    def turn(
        self, *, name: str, session_id: str, input: object
    ) -> AbstractContextManager[Turn]: ...


class Solver(Protocol):
    """Výpočet plánu pro potvrzenou revizi zakázky (#12)."""

    def solve(self, project: Project) -> CalculationResult: ...


@dataclass(frozen=True, slots=True)
class RoutingRequest:
    """Co router dostane: zpráva a rozpracovaná zakázka (`order_summary`)."""

    message: str
    order: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class RoutingError:
    """Router nerozhodl (výpadek API, chybí klíč, neplatná odpověď); nikdy ne „unclear“."""

    router: str
    detail: str


class Router(Protocol):
    """Rozpoznání úlohy ve zprávě (spec kap. 6, ADR-0004, ADR-0012)."""

    name: str

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]: ...


class ManualRouter:
    """Router bez klasifikace: zpráva jde jediné implementované schopnosti (vždy dostupný).

    Nástroj si uživatel volí sám (karta nástroje, „Zadat ručně“); tady jen pustí zprávu
    do extrakce. Slouží jako poslední záloha a pro běh bez sítě.
    """

    name = "manual"

    def route(self, request: RoutingRequest) -> Result[RoutingDecision, RoutingError]:
        return Ok(
            RoutingDecision(
                outcome=RouteOutcome.SUPPORTED, capability="cutting_1d", router=self.name
            )
        )


@dataclass(frozen=True, slots=True)
class Ports:
    """Všechny adaptéry, které smyčka efektů potřebuje."""

    llm: LlmClient
    prompts: PromptStore
    tracer: Tracer
    solver: Solver
    router: Router = field(default_factory=ManualRouter)
