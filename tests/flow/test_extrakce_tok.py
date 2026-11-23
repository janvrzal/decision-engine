"""UC-01 přes smyčku efektů s falešnými adaptéry: zpráva → extrakce → návrh → plán (#10, #11)."""

import json

import pytest
from fakes import FakeLlm, fake_ports

from decision_engine.app.ports import LlmError
from decision_engine.app.session import handle
from decision_engine.core.events import MessageSent, ProposalConfirmed
from decision_engine.core.state import Step, current_step, initial_state, is_result_stale

pytestmark = pytest.mark.flow

ZADANI = "Deset jeklů po 2 m a pět příček po 1,5 m z šestimetrových tyčí po 420 Kč, prořez 3 mm."

ODPOVED = json.dumps(
    {
        "name": "Jekly a příčky",
        "material": "jekl 40×40",
        "parts": [
            {"name": "jekl", "length_mm": 2000, "quantity": 10},
            {"name": "příčka", "length_mm": 1500, "quantity": 5},
        ],
        "stock": [{"length_mm": 6000, "price": "420", "uncertain": ["length_mm"]}],
        "kerf_mm": 3,
        "reply": "Rozpoznal jsem 2 druhy dílů a tyče 6 m po 420 Kč.",
    },
    ensure_ascii=False,
)


def test_uc01_zprava_az_po_plan() -> None:
    llm = FakeLlm(ODPOVED)
    ports, _, solver = fake_ports(llm)

    state = handle(initial_state("relace-1"), MessageSent(text=ZADANI), ports)

    assert state.proposal is not None
    assert current_step(state) is Step.REVIEW
    assert [part.length_mm for part in state.proposal.parts] == [2000, 1500]
    assert ("problem", "stock", 0, "length_mm") in state.proposal.unconfirmed
    assert state.messages[-1].text.startswith("Rozpoznal jsem")

    state = handle(state, ProposalConfirmed(), ports)

    assert state.project is not None
    assert solver.solved == [state.project]
    assert state.result is not None
    assert not is_result_stale(state)
    assert current_step(state) is Step.RESULT


def test_prompt_obsahuje_zadani_schema_a_prevod_na_mm() -> None:
    llm = FakeLlm(ODPOVED)
    ports, _, _ = fake_ports(llm)

    handle(initial_state("relace-1"), MessageSent(text=ZADANI), ports)

    messages, attempt = llm.calls[0]
    assert attempt == 1
    assert messages[-1].role == "user"
    assert messages[-1].content == ZADANI
    assert '"length_mm"' in messages[0].content  # JSON schéma je dosazené
    assert "{{" not in messages[0].content


def test_opravny_pokus_po_neplatnem_vystupu() -> None:
    llm = FakeLlm('{"parts": [{"length_mm": "dlouhý"}]}', ODPOVED)
    ports, tracer, _ = fake_ports(llm)

    state = handle(initial_state("relace-1"), MessageSent(text=ZADANI), ports)

    assert state.proposal is not None
    assert [attempt for _, attempt in llm.calls] == [1, 2]
    repair = llm.calls[1][0][-1].content
    assert "parts.0.length_mm" in repair
    extraction = tracer.turns[0].metadata["extraction"]
    assert isinstance(extraction, dict)
    assert extraction["attempts"] == 2


def test_dva_neplatne_vystupy_jsou_chyba_ai_a_data_zustanou() -> None:
    llm = FakeLlm("není json", "pořád není json")
    ports, tracer, _ = fake_ports(llm)

    state = handle(initial_state("relace-1"), MessageSent(text=ZADANI), ports)

    assert state.proposal is None
    assert state.messages[-1].error_kind == "invalid_response"
    assert tracer.turns[0].error is not None


def test_vypadek_modelu_je_chyba_pripojeni_bez_opakovani() -> None:
    llm = FakeLlm(LlmError(kind="connection", detail="timeout"))
    ports, _, _ = fake_ports(llm)

    state = handle(initial_state("relace-1"), MessageSent(text=ZADANI), ports)

    assert len(llm.calls) == 1
    assert state.messages[-1].error_kind == "connection"
    assert state.pending is None


def test_trace_kola_ma_session_vstup_vystup_a_metadata() -> None:
    llm = FakeLlm(ODPOVED)
    ports, tracer, _ = fake_ports(llm)

    handle(initial_state("relace-7"), MessageSent(text=ZADANI), ports)

    (turn,) = tracer.turns
    assert turn.name == "process-message"
    assert turn.session_id == "relace-7"
    assert turn.input == ZADANI
    assert turn.output == "Rozpoznal jsem 2 druhy dílů a tyče 6 m po 420 Kč."
    assert turn.metadata["step"] == "review"
    assert turn.error is None


def test_udalost_bez_ai_trace_nevytvori() -> None:
    ports, tracer, _ = fake_ports(FakeLlm())

    handle(initial_state("relace-1"), ProposalConfirmed(), ports)

    assert tracer.turns == []
