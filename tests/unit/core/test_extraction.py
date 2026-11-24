"""Testy převodu výstupu modelu na návrh změny: id, výchozí hodnoty a nepotvrzené hodnoty (R6)."""

from decimal import Decimal
from typing import Any

from decision_engine.core.extraction import (
    DEFAULT_MIN_REMNANT_MM,
    DEFAULT_STOCK_LENGTH_MM,
    ExtractionOutput,
    empty_proposal,
    proposal_from_extraction,
)
from decision_engine.core.model.cutting_1d import Objective, Project


def _output(**data: Any) -> ExtractionOutput:
    return ExtractionOutput.model_validate(
        {
            "name": "Regál",
            "parts": [{"name": "noha", "length_mm": 1800, "quantity": 4}],
            "stock": [{"length_mm": 6000, "price": "320"}],
            "kerf_mm": 3,
            **data,
        }
    )


def test_nova_zakazka_dostane_id_a_vychozi_hodnoty() -> None:
    proposal = proposal_from_extraction(_output(), base=None)

    assert proposal.base_revision is None
    assert [part.id for part in proposal.parts] == ["p1"]
    assert [stock.id for stock in proposal.stock] == ["s1"]
    assert proposal.parameters.min_remnant_mm == DEFAULT_MIN_REMNANT_MM
    assert proposal.parameters.trim_mm == 0
    assert proposal.parameters.kerf_mm == 3
    assert proposal.unconfirmed == {
        ("parameters", "trim_mm"),
        ("parameters", "min_remnant_mm"),
        ("parameters", "objective"),
    }


def test_vychozi_cil_je_nejnizsi_cena_jen_s_cenami_vsech_delek() -> None:
    with_prices = proposal_from_extraction(_output(), base=None)
    without = proposal_from_extraction(
        _output(stock=[{"length_mm": 6000}, {"length_mm": 3000, "price": "150"}]), base=None
    )

    assert with_prices.parameters.objective is Objective.CHEAPEST
    assert without.parameters.objective is Objective.LEAST_MATERIAL


def test_cil_od_uzivatele_neni_nepotvrzeny() -> None:
    proposal = proposal_from_extraction(_output(objective="fewest_bars"), base=None)

    assert proposal.parameters.objective is Objective.FEWEST_BARS
    assert ("parameters", "objective") not in proposal.unconfirmed


def test_chybejici_skladova_delka_se_nabidne_jako_nepotvrzena() -> None:
    proposal = proposal_from_extraction(_output(stock=[]), base=None)

    assert proposal.stock[0].length_mm == DEFAULT_STOCK_LENGTH_MM
    assert ("problem", "stock", 0, "length_mm") in proposal.unconfirmed


def test_chybejici_prorez_zustane_prazdny() -> None:
    # Prořez nemá ve specifikaci výchozí hodnotu; uživatel ho doplní.
    proposal = proposal_from_extraction(_output(kerf_mm=None), base=None)

    assert proposal.parameters.kerf_mm is None


def test_odhad_modelu_je_nepotvrzeny() -> None:
    output = _output(
        stock=[{"length_mm": 6000, "price": "320", "uncertain": ["length_mm"]}],
        parts=[{"name": "noha", "length_mm": 1800, "quantity": 4, "uncertain": ["quantity"]}],
    )

    proposal = proposal_from_extraction(output, base=None)

    assert ("problem", "stock", 0, "length_mm") in proposal.unconfirmed
    assert ("problem", "parts", 0, "quantity") in proposal.unconfirmed


def test_uprava_zachova_id_a_nove_polozce_prideli_volne(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)  # díly p1, p2, skladová délka s1
    output = _output(
        parts=[
            {"ref": "p2", "name": "polička", "length_mm": 1250, "quantity": 8},
            {"name": "příčka", "length_mm": 850, "quantity": 2},
        ],
        stock=[{"ref": "s1", "length_mm": 6000, "price": "320"}],
    )

    proposal = proposal_from_extraction(output, base)

    assert [part.id for part in proposal.parts] == ["p2", "p3"]
    assert proposal.base_revision == base.revision
    assert proposal.stock[0].price == Decimal("320")


def test_neznamy_ref_dostane_nove_id() -> None:
    output = _output(parts=[{"ref": "x9", "name": "noha", "length_mm": 1800, "quantity": 4}])

    proposal = proposal_from_extraction(output, base=None)

    assert proposal.parts[0].id == "p1"


def test_navrh_bez_nazvu_prevezme_nazev_zakazky(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)

    proposal = proposal_from_extraction(_output(name=None), base)

    assert proposal.name == base.name


def test_nova_zakazka_bez_nazvu_dostane_vychozi_nazev() -> None:
    proposal = proposal_from_extraction(_output(name=None), base=None)

    assert proposal.name == "Nová zakázka"


def test_extra_pole_od_modelu_nevadi() -> None:
    output = ExtractionOutput.model_validate({"parts": [], "poznamka": "navíc"})

    assert output.parts == ()


def test_prazdny_navrh_pro_rucni_zadani_ma_vychozi_hodnoty_jako_ai() -> None:
    proposal = empty_proposal()

    assert proposal.origin == "manual"
    assert proposal.parts == ()
    assert proposal.stock[0].length_mm == DEFAULT_STOCK_LENGTH_MM
    assert proposal.parameters.kerf_mm is None
    assert proposal.parameters.objective is Objective.LEAST_MATERIAL
    assert ("problem", "stock", 0, "length_mm") in proposal.unconfirmed


def _changed_base(project_data: dict[str, Any]) -> Project:
    """Potvrzená zakázka s materiálem a ručně upravenými parametry."""
    data = {
        **project_data,
        "problem": {**project_data["problem"], "material": "jekl 40×40×2"},
        "parameters": {
            **project_data["parameters"],
            "kerf_mm": 2,
            "trim_mm": 10,
            "min_remnant_mm": 500,
            "objective": "fewest_bars",
            "time_limit_s": 20,
        },
    }
    return Project.model_validate(data)


def test_navazujici_zmena_zachova_material_a_parametry(project_data: dict[str, Any]) -> None:
    base = _changed_base(project_data)
    output = ExtractionOutput.model_validate(
        {"parts": [{"ref": "p1", "name": "noha", "length_mm": 1800, "quantity": 6}]}
    )

    proposal = proposal_from_extraction(output, base)

    assert proposal.material == "jekl 40×40×2"
    params = proposal.parameters
    assert (params.kerf_mm, params.trim_mm, params.min_remnant_mm) == (2, 10, 500)
    assert params.objective is Objective.FEWEST_BARS
    assert params.time_limit_s == 20
    assert [item.id for item in proposal.stock] == [item.id for item in base.problem.stock]
    assert not any(path[0] == "parameters" for path in proposal.unconfirmed)
    assert not any(path[:2] == ("problem", "stock") for path in proposal.unconfirmed)


def test_navazujici_zmena_prevezme_jen_to_co_uzivatel_rekl(project_data: dict[str, Any]) -> None:
    base = _changed_base(project_data)
    output = ExtractionOutput.model_validate(
        {
            "material": "jekl 30×30×2",
            "parts": [{"ref": "p1", "name": "noha", "length_mm": 1800, "quantity": 4}],
            "kerf_mm": 3,
        }
    )

    proposal = proposal_from_extraction(output, base)

    assert proposal.material == "jekl 30×30×2"
    assert proposal.parameters.kerf_mm == 3
    assert proposal.parameters.trim_mm == 10
