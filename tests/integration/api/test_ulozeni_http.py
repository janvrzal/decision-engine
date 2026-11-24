"""Uložení a načtení zakázky přes HTTP (UC-06): soubor, hlavičky, chyby a round-trip."""

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from decision_engine.adapters.config import UnavailableLlm
from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.adapters.noop_tracing import NoopTracer
from decision_engine.api.app import create_app
from decision_engine.api.project_download import file_name
from decision_engine.api.routes import Services
from decision_engine.api.sessions import SessionStore
from decision_engine.app.ports import Ports
from decision_engine.app.solving import RegistrySolver

pytestmark = pytest.mark.integration

PROMPTS = Path(__file__).resolve().parents[3] / "prompts"
EDIT = {
    "type": "ProposalEdited",
    "name": "Regál do dílny",
    "material": "jekl 40×40×2",
    "parts": [{"id": "p1", "name": "noha", "length_mm": 1800, "quantity": 4}],
    "stock": [{"id": "s1", "length_mm": 6000, "price": "320.50"}],
    "parameters": {"kerf_mm": 3, "trim_mm": 0, "min_remnant_mm": 300, "objective": "cheapest"},
}


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


def _planned(client: TestClient) -> str:
    session: str = client.post("/api/sessions").json()["session"]["id"]
    _send(client, session, {"type": "ToolSelected", "capability": "cutting_1d"})
    _send(client, session, EDIT)
    _send(client, session, {"type": "ProposalConfirmed"})
    return session


def test_ulozeni_vrati_soubor_s_nazvem_podle_zakazky() -> None:
    client = _client()
    session = _planned(client)

    response = client.get(f"/api/sessions/{session}/project")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "regal-do-dilny.decision.json" in response.headers["content-disposition"]
    assert response.json()["problem"]["stock"][0]["price"] == "320.50"


def test_ulozit_jde_jen_potvrzenou_zakazku() -> None:
    client = _client()
    session = client.post("/api/sessions").json()["session"]["id"]

    response = client.get(f"/api/sessions/{session}/project")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "no_project"
    assert client.get("/api/sessions/neni/project").status_code == 404


def test_ulozena_zakazka_se_v_nove_relaci_nacte_se_stejnymi_vstupy() -> None:
    client = _client()
    content = client.get(f"/api/sessions/{_planned(client)}/project").text
    fresh = client.post("/api/sessions").json()["session"]["id"]

    view = _send(client, fresh, {"type": "ProjectImported", "content": content})

    assert view["project"]["step"] == "review"
    assert view["proposal"]["origin"] == "file"
    assert view["proposal"]["objective"] == "cheapest"
    assert view["proposal"]["stock"][0]["price"]["value"] == "320.50"
    assert view["proposal"]["can_confirm"] is True
    assert view["messages"][0]["text"].startswith("Zakázka načtena")
    view = _send(client, fresh, {"type": "ProposalConfirmed"})
    assert view["result"] is not None


def test_neplatny_soubor_vrati_chybu_a_zakazku_nezmeni() -> None:
    client = _client()
    session = _planned(client)

    view = _send(client, session, {"type": "ProjectImported", "content": "{}"})

    assert view["import_error"] == "Soubor není zakázka DecisionEngine."
    assert view["project"]["step"] == "result"
    assert view["result"] is not None


def test_rozpracovany_navrh_neni_soucasti_souboru_a_ui_to_rekne() -> None:
    client = _client()
    session = _planned(client)

    view = _send(client, session, {"type": "EditRequested"})

    assert view["project"]["can_save"] is True
    assert view["project"]["save_note"] == "Rozpracované změny v návrhu nebudou součástí souboru."


def test_prilis_velky_soubor_odmitne_api() -> None:
    client = _client()
    session = client.post("/api/sessions").json()["session"]["id"]

    event = {"type": "ProjectImported", "content": "x" * 1_000_001}
    assert client.post(f"/api/sessions/{session}/events", json=event).status_code == 422


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Regál do dílny", "regal-do-dilny.decision.json"),
        ("  Plot / zahrada 2026 ", "plot-zahrada-2026.decision.json"),
        ("***", "zakazka.decision.json"),
    ],
)
def test_nazev_souboru_bez_diakritiky(name: str, expected: str) -> None:
    assert file_name(name) == expected
