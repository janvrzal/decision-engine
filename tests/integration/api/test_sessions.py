"""Endpointy relací přes HTTP s falešným modelem: celý UC-01 a chybové stavy (#14)."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.adapters.noop_tracing import NoopTracer
from decision_engine.api.app import create_app
from decision_engine.api.routes import Services
from decision_engine.api.sessions import SessionStore
from decision_engine.app.ports import ChatMessage, LlmError, Ports, Prompt
from decision_engine.app.solving import RegistrySolver
from decision_engine.core.result import Err, Ok, Result

pytestmark = pytest.mark.integration

PROMPTS = Path(__file__).resolve().parents[3] / "prompts"
ZADANI = "Deset jeklů po 2 m a pět příček po 1,5 m z tyčí 6 m po 420 Kč, prořez 3 mm."
ODPOVED = json.dumps(
    {
        "name": "Jekly",
        "parts": [
            {"name": "jekl", "length_mm": 2000, "quantity": 10},
            {"name": "příčka", "length_mm": 1500, "quantity": 5},
        ],
        "stock": [{"length_mm": 6000, "price": "420"}],
        "kerf_mm": 3,
        "reply": "Rozpoznal jsem 2 druhy dílů.",
    },
    ensure_ascii=False,
)


class ScriptedLlm:
    def __init__(self, *answers: str | LlmError) -> None:
        self.answers = list(answers)

    def complete_json(
        self, messages: Sequence[ChatMessage], *, prompt: Prompt, attempt: int
    ) -> Result[str, LlmError]:
        answer = self.answers.pop(0)
        return Err(answer) if isinstance(answer, LlmError) else Ok(answer)


def _client(*answers: str | LlmError) -> TestClient:
    ports = Ports(
        llm=ScriptedLlm(*answers),
        prompts=FilePromptStore(PROMPTS),
        tracer=NoopTracer(),
        solver=RegistrySolver(),
    )
    services = Services(
        store=SessionStore(), ports=ports, extraction_available=True, on_shutdown=lambda: None
    )
    return TestClient(create_app(static_dir=None, services=services))


def _send(client: TestClient, session: str, event: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"/api/sessions/{session}/events", json=event)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def _steps(view: dict[str, Any]) -> dict[str, str]:
    return {step["id"]: step["state"] for step in view["project"]["steps"]}


def test_uc01_cely_tok_pres_http() -> None:
    client = _client(ODPOVED)
    view = client.post("/api/sessions").json()
    session = view["session"]["id"]
    assert view["project"]["step"] == "input"
    assert view["project"]["name"] == "Nová zakázka"
    assert [c["label"] for c in view["capabilities"]] == ["Řezání tyčí"]

    view = _send(client, session, {"type": "MessageSent", "text": ZADANI})
    proposal = view["proposal"]
    assert view["project"]["step"] == "review"
    assert _steps(view) == {"input": "done", "review": "active", "result": "unavailable"}
    assert [p["length_mm"]["value"] for p in proposal["parts"]] == [2000, 1500]
    assert proposal["parameters"]["min_remnant_mm"] == {
        "value": 300,
        "unconfirmed": True,
        "error": None,
        "previous": None,
    }
    assert proposal["stock"][0]["price"]["value"] == "420"
    assert proposal["can_confirm"] is True
    assert view["messages"][-1]["text"] == "Rozpoznal jsem 2 druhy dílů."

    edited = {
        "type": "ProposalEdited",
        "name": "Jekly",
        "material": None,
        "parts": [
            {"id": "p1", "name": "jekl", "length_mm": 2000, "quantity": 10},
            {"id": "p2", "name": "příčka", "length_mm": 1500, "quantity": 5},
        ],
        "stock": [{"id": "s1", "length_mm": 6000, "price": "420"}],
        "parameters": {"kerf_mm": 3, "trim_mm": 0, "min_remnant_mm": 400, "objective": "cheapest"},
    }
    view = _send(client, session, edited)
    assert view["proposal"]["parameters"]["min_remnant_mm"]["unconfirmed"] is False

    view = _send(client, session, {"type": "ProposalConfirmed"})
    result = view["result"]
    assert view["project"]["step"] == "result"
    assert view["project"]["revision"] == 0
    assert _steps(view) == {"input": "done", "review": "done", "result": "active"}
    assert result["status"] == "best_found"
    assert result["status_label"] == "Nejlepší nalezený"
    assert result["stale"] is False
    assert result["svg"].startswith("<svg")
    assert result["metrics"]["bars_used"] == 5
    assert result["bars"][0]["numbers"] == [1, 2, 3, 4, 5]
    assert result["bars"][0]["cuts_mm"] == ["2000", "4003", "5506"]
    assert result["bars"][0]["tail"] == "remnant"
    assert view["pending_operation"] is None


def test_nepotvrzeny_navrh_zneplatni_plan_a_zahozeni_ho_vrati() -> None:
    client = _client(ODPOVED, ODPOVED)
    session = client.post("/api/sessions").json()["session"]["id"]
    _send(client, session, {"type": "MessageSent", "text": ZADANI})
    planned = _send(client, session, {"type": "ProposalConfirmed"})

    view = _send(client, session, {"type": "MessageSent", "text": "Ať jsou příčky 1,6 m."})
    assert view["result"]["stale"] is True
    assert view["result"]["stale_reason"] == "čekají nepotvrzené změny"
    assert view["proposal"]["is_change"] is True
    assert _steps(view)["result"] == "stale"
    assert view["result"]["metrics"] == planned["result"]["metrics"]

    view = _send(client, session, {"type": "ProposalRejected"})
    assert view["result"]["stale"] is False
    assert view["proposal"] is None


def test_neplatny_navrh_nejde_potvrdit_a_rekne_proc() -> None:
    bez_delky = json.dumps({"parts": [{"name": "jekl", "quantity": 2}], "kerf_mm": 3})
    client = _client(bez_delky)
    session = client.post("/api/sessions").json()["session"]["id"]

    view = _send(client, session, {"type": "MessageSent", "text": "dva jekly"})

    proposal = view["proposal"]
    assert proposal["can_confirm"] is False
    assert proposal["confirm_disabled_reason"] == "Opravte 1 pole, než spustíte výpočet."
    assert proposal["errors"] == [
        {"field": "Díl 1, délka", "message": "Chybí hodnota.", "target": "parts.0.length_mm"}
    ]
    assert proposal["parts"][0]["length_mm"]["error"] == "Chybí hodnota."
    # Skladová délka chyběla → výchozí 6 000 mm jako nepotvrzená (UC-01 A2).
    assert proposal["stock"][0]["length_mm"] == {
        "value": 6000,
        "unconfirmed": True,
        "error": None,
        "previous": None,
    }
    cheapest = proposal["objective_options"][0]
    assert cheapest["value"] == "cheapest"
    assert cheapest["disabled_reason"] == "Chybí ceny skladových délek."

    view = _send(client, session, {"type": "ProposalConfirmed"})
    assert view["result"] is None
    assert view["project"]["revision"] is None


def test_vypadek_ai_je_cesky_a_data_zustanou() -> None:
    client = _client(LlmError(kind="rate_limit", detail="429"))
    session = client.post("/api/sessions").json()["session"]["id"]

    view = _send(client, session, {"type": "MessageSent", "text": ZADANI})

    assert view["messages"][-1]["kind"] == "error"
    assert "moc požadavků najednou" in view["messages"][-1]["text"]
    assert view["proposal"] is None
    assert view["pending_operation"] is None


def test_get_vrati_stejny_stav() -> None:
    client = _client(ODPOVED)
    session = client.post("/api/sessions").json()["session"]["id"]
    after = _send(client, session, {"type": "MessageSent", "text": ZADANI})

    assert client.get(f"/api/sessions/{session}").json() == after


def test_neznama_relace_je_404() -> None:
    client = _client()

    response = client.get("/api/sessions/neexistuje")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "session_not_found"
    assert client.post("/api/sessions/x/events", json={"type": "SolveRequested"}).status_code == 404


@pytest.mark.parametrize(
    "event",
    [
        {"type": "SolveFinished", "result": {}},
        {"type": "AiFailed", "kind": "connection"},
        {"type": "ProposalReceived", "proposal": {"base_revision": None}},
        {"type": "Neznama"},
    ],
)
def test_udalost_z_efektu_nejde_poslat_zvenku(event: dict[str, Any]) -> None:
    client = _client()
    session = client.post("/api/sessions").json()["session"]["id"]

    assert client.post(f"/api/sessions/{session}/events", json=event).status_code == 422


def test_prazdna_zprava_nic_neudela() -> None:
    client = _client()
    session = client.post("/api/sessions").json()["session"]["id"]

    view = _send(client, session, {"type": "MessageSent", "text": "   "})

    assert view["messages"] == []


def test_openapi_obsahuje_relace_a_view_model() -> None:
    schema = _client().get("/openapi.json").json()

    paths = set(schema["paths"])
    assert "/api/sessions" in paths
    assert "/api/sessions/{session_id}" in paths
    assert "/api/sessions/{session_id}/events" in paths
    assert "ViewModel" in schema["components"]["schemas"]
