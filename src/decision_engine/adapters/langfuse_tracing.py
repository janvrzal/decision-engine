"""Trasování do Langfuse (ADR-0009, Langfuse best practices).

Jedno kolo dialogu = jeden trace s kořenovou observation `process-message` (typ `chain`).
Relace aplikace = session v Langfuse. Volání modelu uvnitř kola zaznamená integrace
`langfuse.openai` jako vnořené `generation` (model, tokeny, cena, latence, chyba).
"""

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Any

from langfuse import Langfuse, propagate_attributes


class LangfuseTurn:
    """Kořenová observation kola; metadata se slučují."""

    def __init__(self, observation: Any) -> None:
        self._observation = observation
        self._metadata: dict[str, object] = {}

    def set_output(self, output: object) -> None:
        self._observation.update(output=output)

    def set_metadata(self, metadata: Mapping[str, object]) -> None:
        self._metadata.update(metadata)
        self._observation.update(metadata=self._metadata)

    def fail(self, message: str) -> None:
        self._observation.update(level="ERROR", status_message=message)


class LangfuseTracer:
    """`Tracer` nad klientem Langfuse."""

    def __init__(self, client: Langfuse) -> None:
        self._client = client

    @contextmanager
    def turn(self, *, name: str, session_id: str, input: object) -> Generator[LangfuseTurn]:
        with (
            self._client.start_as_current_observation(
                name=name, as_type="chain", input=input
            ) as observation,
            propagate_attributes(session_id=session_id),
        ):
            yield LangfuseTurn(observation)

    def flush(self) -> None:
        """Odešle frontu událostí; potřeba jen u krátce běžících skriptů."""
        self._client.flush()
