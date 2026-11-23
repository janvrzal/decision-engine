"""Skutečné volání modelu (placené API), jen na vyžádání.

uv run --env-file .env pytest -m ai
"""

import os

import pytest

from decision_engine.adapters.config import build_ai_adapters
from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.app.extractor import run_extraction
from decision_engine.app.ports import Ports
from decision_engine.app.solving import RegistrySolver
from decision_engine.core.effects import CallExtractor
from decision_engine.core.events import ProposalReceived

pytestmark = pytest.mark.ai


@pytest.mark.skipif(not os.environ.get("LLM_API_KEY"), reason="chybí LLM_API_KEY")
def test_zadani_uc01_se_prevede_na_navrh() -> None:
    ai = build_ai_adapters()
    ports = Ports(llm=ai.llm, prompts=ai.prompts, tracer=ai.tracer, solver=RegistrySolver())
    text = "Deset jeklů po 2 m a pět příček po 1,5 m z šestimetrových tyčí po 420 Kč."

    event, _ = run_extraction(CallExtractor(text=text, base=None), ports)
    ai.tracer.flush()

    assert isinstance(event, ProposalReceived)
    parts = sorted((p.length_mm, p.quantity) for p in event.proposal.parts)
    assert parts == [(1500, 5), (2000, 10)]
    assert [s.length_mm for s in event.proposal.stock] == [6000]
    assert isinstance(ports.prompts, FilePromptStore) or ai.langfuse_enabled
