"""Změny návrhu oproti potvrzené revizi (spec kap. 4, souhrn změn)."""

from decimal import Decimal
from typing import Any

from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import PartDraft, proposal_from_project
from decision_engine.core.model.proposal_diff import diff_proposal


def test_beze_zmeny_je_diff_prazdny(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)

    assert diff_proposal(proposal_from_project(base), base).empty


def test_pridany_zmeneny_a_odebrany_dil(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)  # díly p1, p2
    proposal = proposal_from_project(base)
    first = proposal.parts[0].model_copy(update={"quantity": 6})
    added = PartDraft(id="p3", name="příčka", length_mm=850, quantity=4)
    proposal = proposal.model_copy(update={"parts": (first, added)})

    diff = diff_proposal(proposal, base)

    assert diff.added_parts == ("p3",)
    assert [p.id for p in diff.removed_parts] == ["p2"]
    (change,) = [c for c in diff.changed if c.path[:2] == ("problem", "parts")]
    assert change.path == ("problem", "parts", 0, "quantity")
    assert change.after == 6


def test_zmena_parametru_a_materialu(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)
    proposal = proposal_from_project(base)
    params = proposal.parameters.model_copy(
        update={"kerf_mm": Decimal("2.5"), "objective": Objective.FEWEST_BARS}
    )
    proposal = proposal.model_copy(update={"parameters": params, "material": "jekl 30×30"})

    paths = {c.path for c in diff_proposal(proposal, base).changed}

    assert ("parameters", "kerf_mm") in paths
    assert ("parameters", "objective") in paths
    assert ("problem", "material") in paths


def test_presun_radku_neni_zmena(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)
    proposal = proposal_from_project(base)
    proposal = proposal.model_copy(update={"parts": tuple(reversed(proposal.parts))})

    assert diff_proposal(proposal, base).empty
