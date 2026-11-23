"""Testy aplikace FastAPI: health, servírování SPA a export OpenAPI."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from decision_engine.api.app import create_app
from decision_engine.api.openapi import main as export_openapi

pytestmark = pytest.mark.integration


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    build = tmp_path / "build"
    (build / "_app").mkdir(parents=True)
    (build / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
    (build / "_app" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "tajne.txt").write_text("tajné", encoding="utf-8")
    return build


def test_health_vraci_ok_a_verzi() -> None:
    response = TestClient(create_app(static_dir=None)).get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_neznamy_endpoint_api_je_404_json(static_dir: Path) -> None:
    response = TestClient(create_app(static_dir)).get("/api/neexistuje")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


def test_staticky_soubor_se_servi(static_dir: Path) -> None:
    response = TestClient(create_app(static_dir)).get("/_app/app.js")

    assert response.status_code == 200
    assert response.text == "console.log(1)"


@pytest.mark.parametrize("path", ["/", "/zakazka/123", "/neco.js"])
def test_ostatni_cesty_vraci_index_spa(static_dir: Path, path: str) -> None:
    response = TestClient(create_app(static_dir)).get(path)

    assert response.status_code == 200
    assert response.text == "<html>SPA</html>"


def test_cesta_mimo_build_se_neservi(static_dir: Path) -> None:
    response = TestClient(create_app(static_dir)).get("/..%2Ftajne.txt")

    assert "tajné" not in response.text


def test_bez_sestaveneho_frontendu_poradi_co_delat(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 503
    assert "pnpm build" in response.text


def test_export_openapi_obsahuje_health(tmp_path: Path) -> None:
    output = tmp_path / "openapi.json"

    export_openapi([str(output)])

    schema = json.loads(output.read_text(encoding="utf-8"))
    assert "/api/health" in schema["paths"]
    assert not any(path.startswith("/{") for path in schema["paths"])
