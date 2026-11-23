"""Testy datových objektů 1D: neměnnost, jednotky a hranice hodnot (ADR-0001, ADR-0002)."""

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from decision_engine.core.model.cutting_1d import (
    Objective,
    Part,
    Project,
    StockLength,
)


def test_platna_zakazka_se_nacte(project_data: dict[str, Any]) -> None:
    project = Project.model_validate(project_data)

    assert project.problem.parts[0] == Part(id="p1", name="noha", length_mm=1800, quantity=4)
    assert project.problem.stock[0].price == Decimal("320.00")
    assert project.parameters.objective is Objective.CHEAPEST


def test_kolekce_jsou_tuple(project_data: dict[str, Any]) -> None:
    project = Project.model_validate(project_data)

    assert isinstance(project.problem.parts, tuple)
    assert isinstance(project.problem.stock, tuple)


def test_model_je_nemenny(project_data: dict[str, Any]) -> None:
    project = Project.model_validate(project_data)

    field = "name"
    with pytest.raises(ValidationError):
        setattr(project, field, "jiný")


def test_chybejici_cena_neni_nula() -> None:
    stock = StockLength(id="s1", length_mm=6000, price=None)

    assert stock.price is None


@pytest.mark.parametrize("length", [0, -1])
def test_delka_dilu_musi_byt_kladna(length: int) -> None:
    with pytest.raises(ValidationError):
        Part(id="p1", name="noha", length_mm=length, quantity=1)


def test_delka_neni_desetinne_cislo() -> None:
    with pytest.raises(ValidationError):
        Part.model_validate({"id": "p1", "name": "noha", "length_mm": 1850.5, "quantity": 1})


def test_delka_z_json_retezce_se_prevede_na_int() -> None:
    part = Part.model_validate({"id": "p1", "name": "noha", "length_mm": "1850", "quantity": 1})

    assert part.length_mm == 1850


def test_pocet_musi_byt_kladny() -> None:
    with pytest.raises(ValidationError):
        Part(id="p1", name="noha", length_mm=100, quantity=0)


def test_nazev_dilu_nesmi_byt_prazdny() -> None:
    with pytest.raises(ValidationError):
        Part(id="p1", name="  ", length_mm=100, quantity=1)


def test_cena_ma_nejvys_dve_desetinna_mista() -> None:
    with pytest.raises(ValidationError):
        StockLength.model_validate({"id": "s1", "length_mm": 6000, "price": "1.005"})


def test_cena_nesmi_byt_zaporna() -> None:
    with pytest.raises(ValidationError):
        StockLength.model_validate({"id": "s1", "length_mm": 6000, "price": "-1"})


def test_nezname_pole_se_odmitne(project_data: dict[str, Any]) -> None:
    project_data["problem"]["parts"][0]["color"] = "červená"

    with pytest.raises(ValidationError):
        Project.model_validate(project_data)


def test_zakazka_potrebuje_aspon_jeden_dil(project_data: dict[str, Any]) -> None:
    project_data["problem"]["parts"] = []

    with pytest.raises(ValidationError):
        Project.model_validate(project_data)


def test_zakazka_potrebuje_aspon_jednu_skladovou_delku(project_data: dict[str, Any]) -> None:
    project_data["problem"]["stock"] = []

    with pytest.raises(ValidationError):
        Project.model_validate(project_data)


def test_neznamy_cil_se_odmitne(project_data: dict[str, Any]) -> None:
    project_data["parameters"]["objective"] = "nejlevnejsi"

    with pytest.raises(ValidationError):
        Project.model_validate(project_data)


def test_neznama_verze_formatu_se_odmitne(project_data: dict[str, Any]) -> None:
    project_data["format_version"] = 2

    with pytest.raises(ValidationError):
        Project.model_validate(project_data)


def test_prorez_a_orez_mohou_byt_nulove(project_data: dict[str, Any]) -> None:
    project_data["parameters"] |= {"kerf_mm": 0, "trim_mm": 0, "min_remnant_mm": 0}

    project = Project.model_validate(project_data)

    assert project.parameters.kerf_mm == 0
