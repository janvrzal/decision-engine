"""Testy převodu vstupu na zakázku a doménové validace 1D: chyby po polích, česky."""

from typing import Any

import pytest

from decision_engine.core.errors import FieldError
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.result import Err, Ok
from decision_engine.core.validation.cutting_1d import NBSP, parse_project


def _errors(data: object) -> tuple[FieldError, ...]:
    match parse_project(data):
        case Ok(project):
            pytest.fail(f"čekal jsem chyby, zakázka prošla: {project}")
        case Err(errors):
            return errors


def _by_path(errors: tuple[FieldError, ...]) -> dict[tuple[str | int, ...], FieldError]:
    return {error.path: error for error in errors}


def test_platna_zakazka_projde(project_data: dict[str, Any]) -> None:
    assert parse_project(project_data) == Ok(Project.model_validate(project_data))


def test_dil_delsi_nez_vsechny_tyce_neni_chyba(project_data: dict[str, Any]) -> None:
    # UC-01: příliš dlouhý díl je neumístěný kus v částečném plánu, ne neplatný vstup.
    project_data["problem"]["parts"][0]["length_mm"] = 7000

    assert isinstance(parse_project(project_data), Ok)


_DELETE = object()
"""Hodnota pro `_set`: pole ze vstupu odstraní."""


def _set(data: dict[str, Any], path: tuple[str | int, ...], value: object) -> None:
    """Nastaví (nebo s `_DELETE` odstraní) hodnotu ve vnořeném vstupu JSON."""
    target: Any = data
    for key in path[:-1]:
        target = target[key]
    if value is _DELETE:
        del target[path[-1]]
    else:
        target[path[-1]] = value


@pytest.mark.parametrize(
    ("path", "value", "code", "message"),
    [
        (("problem", "parts", 1, "length_mm"), _DELETE, "required", "Chybí hodnota."),
        (("problem", "parts", 0, "length_mm"), 0, "too_small", "Hodnota musí být větší než 0."),
        (("problem", "parts", 0, "quantity"), -2, "too_small", "Hodnota musí být větší než 0."),
        (("parameters", "kerf_mm"), -1, "too_small", "Hodnota musí být alespoň 0."),
        (
            ("problem", "parts", 0, "length_mm"),
            1850.5,
            "not_integer",
            "Zadejte celé číslo v milimetrech.",
        ),
        (
            ("problem", "parts", 0, "length_mm"),
            "dlouhá",
            "not_integer",
            "Zadejte celé číslo v milimetrech.",
        ),
        (("problem", "parts", 0, "quantity"), 2.5, "not_integer", "Zadejte celé číslo."),
        (
            ("problem", "stock", 0, "price"),
            "1.005",
            "too_precise",
            "Částka smí mít nejvýš 2 desetinná místa.",
        ),
        (("problem", "stock", 0, "price"), "levně", "not_number", "Zadejte číslo."),
        (("problem", "parts", 0, "name"), "", "required", "Chybí hodnota."),
        (("problem", "parts"), [], "empty", "Seznam nesmí být prázdný."),
        (("parameters", "objective"), "nejlevnejsi", "invalid_choice", "Neznámá volba."),
        (("problem", "parts", 0, "barva"), "modrá", "unknown_field", "Neznámé pole."),
    ],
)
def test_chyba_typu_ma_cestu_kod_a_ceskou_hlasku(
    project_data: dict[str, Any],
    path: tuple[str | int, ...],
    value: object,
    code: str,
    message: str,
) -> None:
    _set(project_data, path, value)

    error = _by_path(_errors(project_data))[path]

    assert (error.code, error.message) == (code, message)


def test_vice_chyb_najednou(project_data: dict[str, Any]) -> None:
    project_data["problem"]["parts"][0]["length_mm"] = 0
    project_data["parameters"]["kerf_mm"] = -1

    assert len(_errors(project_data)) == 2


def test_jediny_neplatny_dil_nehlasi_prazdny_seznam(project_data: dict[str, Any]) -> None:
    project_data["problem"]["parts"] = [{"id": "p1", "name": "noha", "quantity": 1}]

    errors = _errors(project_data)

    assert [error.path for error in errors] == [("problem", "parts", 0, "length_mm")]


def test_vstup_ktery_neni_slovnik_vrati_chybu() -> None:
    errors = _errors(["není", "slovník"])

    assert errors[0].path == ()


def test_duplicitni_id_dilu(project_data: dict[str, Any]) -> None:
    project_data["problem"]["parts"][1]["id"] = "p1"

    error = _by_path(_errors(project_data))[("problem", "parts", 1, "id")]

    assert error.code == "duplicate_id"
    assert error.message == "Tento identifikátor už má jiný díl."


def test_duplicitni_id_skladove_delky(project_data: dict[str, Any]) -> None:
    project_data["problem"]["stock"].append({"id": "s1", "length_mm": 3000, "price": "150"})

    error = _by_path(_errors(project_data))[("problem", "stock", 1, "id")]

    assert error.code == "duplicate_id"


def test_orez_nesmi_byt_delsi_nez_tyc(project_data: dict[str, Any]) -> None:
    project_data["parameters"]["trim_mm"] = 6000

    error = _by_path(_errors(project_data))[("parameters", "trim_mm")]

    assert error.code == "trim_too_long"
    assert error.message == (
        "Ořez musí být kratší než nejkratší skladová délka (6\u00a0000\u00a0mm)."
    )


def test_nejnizsi_cena_vyzaduje_vsechny_ceny(project_data: dict[str, Any]) -> None:
    project_data["problem"]["stock"] = [
        {"id": "s1", "length_mm": 6000, "price": "320"},
        {"id": "s2", "length_mm": 3000, "price": None},
        {"id": "s3", "length_mm": 4000, "price": None},
    ]

    errors = _by_path(_errors(project_data))

    assert set(errors) == {("problem", "stock", 1, "price"), ("problem", "stock", 2, "price")}
    assert errors[("problem", "stock", 1, "price")].code == "missing_price"
    assert errors[("problem", "stock", 1, "price")].message == (
        "Pro cíl „Nejnižší cena“ doplňte cenu, nebo zvolte jiný cíl."
    )


def test_bez_cen_projde_cil_nejmene_materialu(project_data: dict[str, Any]) -> None:
    project_data["problem"]["stock"][0]["price"] = None
    project_data["parameters"]["objective"] = "least_material"

    assert isinstance(parse_project(project_data), Ok)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("problem", "parts", 0, "quantity"), 10_001, f"Hodnota smí být nejvýš 10{NBSP}000."),
        (("problem", "parts", 0, "length_mm"), 100_001, f"Hodnota smí být nejvýš 100{NBSP}000."),
        (
            ("problem", "stock", 0, "price"),
            "10000000.01",
            f"Hodnota smí být nejvýš 10{NBSP}000{NBSP}000.",
        ),
        (("parameters", "time_limit_s"), 121, "Hodnota smí být nejvýš 120."),
        (("problem", "parts", 0, "name"), "x" * 201, "Text smí mít nejvýš 200 znaků."),
    ],
)
def test_prilis_velka_hodnota_ma_ceskou_hlasku(
    project_data: dict[str, Any], path: tuple[str | int, ...], value: object, message: str
) -> None:
    _set(project_data, path, value)

    errors = _by_path(_errors(project_data))

    assert errors[path].code == "too_large" or errors[path].code == "too_long"
    assert errors[path].message == message


def test_prilis_mnoho_kusu_v_zakazce_je_chyba(project_data: dict[str, Any]) -> None:
    for part in project_data["problem"]["parts"]:
        part["quantity"] = 4_000

    errors = _by_path(_errors(project_data))

    error = errors[("problem", "parts")]
    assert error.code == "too_many_pieces"
    assert f"nejvýš 5{NBSP}000" in error.message
