"""Ruční zadání a úprava přes HTTP bez AI (UC-13, UC-07): žádné volání modelu."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from decision_engine.adapters.config import UnavailableLlm
from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.adapters.noop_tracing import NoopTracer
from decision_engine.api.app import create_app
from decision_engine.api.routes import Services
from decision_engine.api.sessions import SessionStore
from decision_engine.app.ports import Ports
from decision_engine.app.solving import RegistrySolver

pytestmark = pytest.mark.integration

PROMPTS = Path(__file__).resolve().parents[3] / "prompts"
PARAMETERS = {"kerf_mm": 3, "trim_mm": 0, "min_remnant_mm": 300, "objective": "least_material"}


def _client() -> TestClient:
    ports = Ports(
        llm=UnavailableLlm(),
        prompts=FilePromptStore(PROMPTS),
        tracer=NoopTracer(),
        solver=RegistrySolver(),
    )
    services = Services(
        store=SessionStore(), ports=ports, extraction_available=False, on_shutdown=lambda: None
    )
    return TestClient(create_app(static_dir=None, services=services))


def _send(client: TestClient, session: str, event: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"/api/sessions/{session}/events", json=event)
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def _edit(parts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "ProposalEdited",
        "name": "Rám",
        "material": None,
        "parts": parts,
        "stock": [{"id": "s1", "length_mm": 6000, "price": None}],
        "parameters": PARAMETERS,
    }


def test_rucni_zadani_az_k_planu_a_uprava_bez_ai() -> None:
    client = _client()
    session = client.post("/api/sessions").json()["session"]["id"]

    view = _send(client, session, {"type": "ToolSelected", "capability": "cutting_1d"})
    assert view["project"]["step"] == "review"
    assert view["proposal"]["origin"] == "manual"
    assert view["proposal"]["parts"] == []

    _send(client, session, _edit([{"id": "p1", "name": "noha", "length_mm": 1800, "quantity": 4}]))
    view = _send(client, session, {"type": "ProposalConfirmed"})
    assert view["project"]["step"] == "result"
    assert view["result"] is not None
    assert view["project"]["can_edit"] is True

    view = _send(client, session, {"type": "EditRequested"})
    assert view["project"]["step"] == "review"
    assert view["proposal"]["is_change"] is True
    assert view["proposal"]["parts"][0]["length_mm"]["value"] == 1800
    assert view["project"]["can_edit"] is False


def test_neznamy_nastroj_je_422() -> None:
    client = _client()
    session = client.post("/api/sessions").json()["session"]["id"]

    event = {"type": "ToolSelected", "capability": "cutting_2d"}
    assert client.post(f"/api/sessions/{session}/events", json=event).status_code == 422
