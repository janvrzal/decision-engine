"""Soubor zakázky (UC-06): uložení, načtení, neplatné soubory (E1) a neplatná data (E2)."""

import json
from decimal import Decimal
from typing import Any

import pytest
from conftest import valid_project_data

from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import ChangeProposal, confirm_proposal
from decision_engine.core.project_file import (
    BROKEN_VALUES,
    NOT_A_PROJECT,
    read_project_file,
    write_project_file,
)
from decision_engine.core.result import Err, Ok


def _project() -> Project:
    return Project.model_validate(valid_project_data())


def _read_ok(content: str) -> ChangeProposal:
    match read_project_file(content):
        case Ok(proposal):
            return proposal
        case Err(message):
            pytest.fail(f"soubor se měl načíst: {message}")


def _read_error(content: str) -> str:
    match read_project_file(content):
        case Ok(proposal):
            pytest.fail(f"soubor se neměl načíst: {proposal}")
        case Err(message):
            return message


def test_ulozena_a_nactena_zakazka_ma_stejne_vstupy_vcetne_cile_a_cen() -> None:
    project = _project()

    proposal = _read_ok(write_project_file(project))

    assert proposal.origin == "file"
    assert proposal.base_revision is None
    assert proposal.unconfirmed == frozenset()
    assert proposal.parameters.objective is Objective.CHEAPEST
    assert proposal.stock[0].price == Decimal("320.00")
    assert confirm_proposal(proposal, project.id, project.revision) == Ok(project)


def test_soubor_je_citelny_json_bez_klicu_a_dialogu() -> None:
    content = write_project_file(_project())

    data = json.loads(content)
    assert data["format_version"] == 1
    assert data["problem"]["stock"][0]["price"] == "320.00"
    assert "Regál do dílny" in content  # čeština bez escapování
    assert set(data) == {
        "id",
        "name",
        "format_version",
        "task_type",
        "revision",
        "problem",
        "parameters",
    }
    for secret in ("key", "token", "messages", "api"):
        assert secret not in content.lower()


def _with(**changes: Any) -> str:
    return json.dumps({**valid_project_data(), **changes}, ensure_ascii=False)


def _without(key: str) -> str:
    data = valid_project_data()
    del data[key]
    return json.dumps(data)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("tohle není json", NOT_A_PROJECT),
        ("[1, 2, 3]", NOT_A_PROJECT),
        ('{"jmeno": "nákupní seznam"}', NOT_A_PROJECT),
        (_without("format_version"), NOT_A_PROJECT),
        (_without("task_type"), NOT_A_PROJECT),
        (_with(format_version="jedna"), NOT_A_PROJECT),
        (
            _with(format_version=2),
            "Soubor je z novější verze aplikace (formát 2), tahle ho neumí načíst.",
        ),
        (
            _with(task_type="cutting_2d"),
            "Soubor obsahuje úlohu, kterou tahle verze aplikace neumí.",
        ),
        (_without("problem"), "V souboru chybí díly a skladové délky."),
        (_with(problem={"parts": []}), "V souboru chybí skladové délky."),
        (_with(problem={"stock": []}), "V souboru chybí díly."),
        (
            _with(problem={"parts": ["díl"], "stock": []}),
            "Některé hodnoty v souboru mají nečekaný tvar, soubor je nejspíš poškozený.",
        ),
        (_with(parameters=[1, 2]), BROKEN_VALUES),
        ("[" * 100_000 + "]" * 100_000, NOT_A_PROJECT),
        ('{"a":' * 50_000, NOT_A_PROJECT),
    ],
)
def test_neplatny_soubor_ma_srozumitelnou_chybu(content: str, message: str) -> None:
    assert _read_error(content) == message


@pytest.mark.parametrize(
    ("change", "path"),
    [
        (("parts", "length_mm", -5), ("problem", "parts", 0, "length_mm")),
        # Cíl „nejnižší cena“ potřebuje ceny všech délek.
        (("stock", "price", None), ("problem", "stock", 0, "price")),
    ],
)
def test_castecne_neplatna_data_se_nactou_jako_navrh_s_chybami(
    change: tuple[str, str, object], path: tuple[str | int, ...]
) -> None:
    collection, field, value = change
    data = valid_project_data()
    data["problem"][collection][0][field] = value

    proposal = _read_ok(json.dumps(data))

    match confirm_proposal(proposal, "zakazka-1", 0):
        case Err(errors):
            assert path in {error.path for error in errors}
        case Ok(_):
            pytest.fail("neplatná data nesmí projít potvrzením")


@pytest.mark.parametrize(
    ("collection", "field", "value"),
    [
        ("parts", "length_mm", "dlouhý"),
        ("parts", "length_mm", 1800.5),
        ("parts", "quantity", True),
        ("stock", "price", "levná"),
    ],
)
def test_hodnota_necekaneho_typu_se_nacte_prazdna_a_oznacena(
    collection: str, field: str, value: object
) -> None:
    data = valid_project_data()
    data["problem"][collection][0][field] = value

    proposal = _read_ok(json.dumps(data))

    path = ("problem", collection, 0, field)
    row = (proposal.parts if collection == "parts" else proposal.stock)[0]
    assert getattr(row, field) is None
    assert path in proposal.file_errors
    assert path in proposal.unconfirmed


def test_neplatny_cil_a_material_se_oznaci_a_zbytek_souboru_se_nacte() -> None:
    data = valid_project_data()
    data["parameters"]["objective"] = "nejkrásnější"
    data["problem"]["material"] = 42

    proposal = _read_ok(json.dumps(data))

    assert proposal.parameters.objective is None
    assert proposal.material is None
    assert {("parameters", "objective"), ("problem", "material")} <= proposal.file_errors
    assert len(proposal.parts) == len(data["problem"]["parts"])


def test_radek_bez_id_dostane_nove_a_nezname_klice_se_ignoruji() -> None:
    data = valid_project_data()
    del data["problem"]["parts"][0]["id"]
    data["problem"]["parts"][0]["poznamka"] = "navíc"

    proposal = _read_ok(json.dumps(data))

    assert proposal.parts[0].id == "p1"
    assert len({part.id for part in proposal.parts}) == len(proposal.parts)


def test_duplicitni_id_se_nacte_a_ukaze_jako_chyba_pri_potvrzeni() -> None:
    data = valid_project_data()
    data["problem"]["parts"].append(dict(data["problem"]["parts"][0]))

    proposal = _read_ok(json.dumps(data))

    match confirm_proposal(proposal, "zakazka-1", 0):
        case Err(errors):
            assert "duplicate_id" in {error.code for error in errors}
        case Ok(_):
            pytest.fail("duplicitní id nesmí projít potvrzením")
