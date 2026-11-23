"""Trasování vypnuté: bez klíčů Langfuse aplikace funguje dál (ADR-0009)."""

from collections.abc import Generator, Mapping
from contextlib import contextmanager


class NoopTurn:
    def set_output(self, output: object) -> None:
        pass

    def set_metadata(self, metadata: Mapping[str, object]) -> None:
        pass

    def fail(self, message: str) -> None:
        pass


class NoopTracer:
    """`Tracer`, který nic nezaznamenává."""

    @contextmanager
    def turn(self, *, name: str, session_id: str, input: object) -> Generator[NoopTurn]:
        yield NoopTurn()

    def flush(self) -> None:
        pass
