"""Falešné adaptéry pro testy toku: bez sítě, klíčů a Langfuse (AGENTS.md pravidlo 11)."""

from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.app.ports import ChatMessage, LlmError, Ports, Prompt
from decision_engine.app.solving import RegistrySolver
from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.result import Err, Ok, Result

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class FakeLlm:
    """Vrací připravené odpovědi v pořadí a zaznamená, co dostal."""

    def __init__(self, *answers: str | LlmError) -> None:
        self._answers = list(answers)
        self.calls: list[tuple[list[ChatMessage], int]] = []

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        self.calls.append((list(messages), attempt))
        answer = self._answers.pop(0)
        return Err(answer) if isinstance(answer, LlmError) else Ok(answer)


class RecordingSolver:
    """Skutečný solver z registru, který si zapamatuje, co počítal."""

    def __init__(self) -> None:
        self.solved: list[Project] = []
        self._solver = RegistrySolver()

    def solve(self, project: Project) -> CalculationResult:
        self.solved.append(project)
        return self._solver.solve(project)


@dataclass
class RecordedTurn:
    name: str
    session_id: str
    input: object
    output: object = None
    metadata: dict[str, object] = field(default_factory=lambda: {})
    error: str | None = None

    def set_output(self, output: object) -> None:
        self.output = output

    def set_metadata(self, metadata: Mapping[str, object]) -> None:
        self.metadata.update(metadata)

    def fail(self, message: str) -> None:
        self.error = message


class RecordingTracer:
    """Zaznamená kola, aby test ověřil obsah trasování."""

    def __init__(self) -> None:
        self.turns: list[RecordedTurn] = []

    @contextmanager
    def turn(self, *, name: str, session_id: str, input: object) -> Generator[RecordedTurn]:
        recorded = RecordedTurn(name=name, session_id=session_id, input=input)
        self.turns.append(recorded)
        yield recorded


def fake_ports(llm: FakeLlm) -> tuple[Ports, RecordingTracer, RecordingSolver]:
    tracer = RecordingTracer()
    solver = RecordingSolver()
    ports = Ports(llm=llm, prompts=FilePromptStore(PROMPTS_DIR), tracer=tracer, solver=solver)
    return ports, tracer, solver
