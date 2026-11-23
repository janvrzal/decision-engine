"""Testy potvrzení návrhu změny: návrh → nová revize zakázky, nebo chyby po polích."""

from decimal import Decimal

import pytest

from decision_engine.core.errors import FieldError
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
    confirm_proposal,
    proposal_from_project,
)
from decision_engine.core.result import Err, Ok


def _proposal(**changes: object) -> ChangeProposal:
    proposal = ChangeProposal(
        base_revision=None,
        name="Regál",
        material=None,
        parts=(PartDraft(id="p1", name="noha", length_mm=1800, quantity=4),),
        stock=(StockLengthDraft(id="s1", length_mm=6000, price=None),),
        parameters=ParametersDraft(
            kerf_mm=3, trim_mm=0, min_remnant_mm=300, objective=Objective.LEAST_MATERIAL
        ),
    )
    return proposal.model_copy(update=changes)


def _errors(proposal: ChangeProposal) -> tuple[FieldError, ...]:
    match confirm_proposal(proposal, "zakazka-1", 0):
        case Ok(project):
            pytest.fail(f"čekal jsem chyby, prošlo: {project}")
        case Err(errors):
            return errors


def test_uplny_navrh_vytvori_revizi() -> None:
    match confirm_proposal(_proposal(), "zakazka-1", 3):
        case Ok(project):
            assert isinstance(project, Project)
            assert project.revision == 3
            assert project.id == "zakazka-1"
            assert project.problem.stock[0].price is None
            assert project.parameters.time_limit_s == 10
        case Err(errors):
            pytest.fail(f"návrh měl projít: {errors}")


def test_chybejici_hodnota_dilu_je_chybi_hodnota() -> None:
    proposal = _proposal(parts=(PartDraft(id="p1", name="noha", quantity=4),))

    (error,) = _errors(proposal)

    assert error.path == ("problem", "parts", 0, "length_mm")
    assert error.message == "Chybí hodnota."


def test_chybejici_nazev_zakazky() -> None:
    (error,) = _errors(_proposal(name=None))

    assert error.path == ("name",)


def test_chybejici_cil_optimalizace() -> None:
    proposal = _proposal(parameters=ParametersDraft(kerf_mm=3, trim_mm=0, min_remnant_mm=0))

    (error,) = _errors(proposal)

    assert error.path == ("parameters", "objective")


def test_navrh_bez_dilu_neprojde() -> None:
    (error,) = _errors(_proposal(parts=()))

    assert error.code == "empty"


def test_cena_z_navrhu_zustane_decimal() -> None:
    proposal = _proposal(stock=(StockLengthDraft(id="s1", length_mm=6000, price=Decimal("1.5")),))

    match confirm_proposal(proposal, "z", 0):
        case Ok(project):
            assert project.problem.stock[0].price == Decimal("1.50")
        case Err(errors):
            pytest.fail(str(errors))


def test_navrh_z_potvrzene_zakazky_ma_stejne_hodnoty_a_projde_potvrzenim() -> None:
    priced = _proposal(stock=(StockLengthDraft(id="s1", length_mm=6000, price=Decimal("320.00")),))
    match confirm_proposal(priced, "zakazka-1", 2):
        case Ok(project):
            proposal = proposal_from_project(project)
            assert proposal.origin == "manual"
            assert proposal.base_revision == 2
            assert proposal.unconfirmed == frozenset()
            assert confirm_proposal(proposal, "zakazka-1", 2) == Ok(project)
        case Err(errors):
            pytest.fail(f"návrh měl projít: {errors}")
