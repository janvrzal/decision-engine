"""Sestavení adaptérů AI z proměnných prostředí (ADR-0008, ADR-0009).

Bez klíčů Langfuse je trasování vypnuté a prompty se berou ze zálohy v `prompts/`.
Bez klíče modelu extrakce vrací chybu připojení; aplikace i testy běží dál.
"""

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from langfuse import Langfuse

from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.adapters.langfuse_prompts import LangfusePromptStore
from decision_engine.adapters.langfuse_tracing import LangfuseTracer
from decision_engine.adapters.llm_openai import OpenAICompatibleLlm
from decision_engine.adapters.llm_replay import ReplayLlm
from decision_engine.adapters.noop_tracing import NoopTracer
from decision_engine.app.ports import ChatMessage, LlmClient, LlmError, Prompt, PromptStore
from decision_engine.core.result import Err, Result

PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_ENVIRONMENT = "development"
SERVICE_NAME = "decision-engine"


class UnavailableLlm:
    """`LlmClient` bez nastaveného klíče modelu: volání skončí chybou, ne pádem."""

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        detail = "Model AI není nastavený (LLM_API_KEY a LLM_MODEL)."
        return Err(LlmError(kind="connection", detail=detail))


@dataclass(frozen=True, slots=True)
class AiAdapters:
    """Adaptéry AI pro `Ports`; `tracer.flush()` odešle trasování před koncem skriptu."""

    llm: LlmClient
    prompts: PromptStore
    tracer: NoopTracer | LangfuseTracer
    langfuse_enabled: bool


def build_ai_adapters(
    environ: Mapping[str, str] | None = None, prompts_dir: Path = PROMPTS_DIR
) -> AiAdapters:
    """Sestaví LLM, prompty a trasování podle prostředí."""
    env: Mapping[str, str] = os.environ if environ is None else environ
    file_prompts = FilePromptStore(prompts_dir)
    langfuse = _langfuse_client(env)

    llm: LlmClient = UnavailableLlm()
    api_key = env.get("LLM_API_KEY", "")
    replay = env.get("LLM_REPLAY_FILE", "")
    if replay:
        # Přehrávané odpovědi pro end-to-end testy a demo; žádné volání AI.
        llm = ReplayLlm.from_file(Path(replay))
    elif api_key and env.get("LLM_MODEL"):
        llm = OpenAICompatibleLlm.create(
            base_url=env.get("LLM_BASE_URL") or DEFAULT_BASE_URL,
            api_key=api_key,
            model=env.get("LLM_MODEL", ""),
            traced=langfuse is not None,
        )

    if langfuse is None:
        return AiAdapters(
            llm=llm, prompts=file_prompts, tracer=NoopTracer(), langfuse_enabled=False
        )
    return AiAdapters(
        llm=llm,
        prompts=LangfusePromptStore(langfuse, file_prompts),
        tracer=LangfuseTracer(langfuse),
        langfuse_enabled=True,
    )


def _langfuse_client(env: Mapping[str, str]) -> Langfuse | None:
    public_key = env.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = env.get("LANGFUSE_SECRET_KEY", "")
    if not (public_key and secret_key):
        return None
    # Název služby v trace (resource atribut OpenTelemetry), jinak „unknown_service“.
    os.environ.setdefault("OTEL_SERVICE_NAME", SERVICE_NAME)
    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        # SDK v5 čte LANGFUSE_BASE_URL; starší název LANGFUSE_HOST přijmeme také.
        base_url=env.get("LANGFUSE_BASE_URL") or env.get("LANGFUSE_HOST") or None,
        environment=env.get("LANGFUSE_TRACING_ENVIRONMENT") or DEFAULT_ENVIRONMENT,
        release=version("decision-engine"),
    )
