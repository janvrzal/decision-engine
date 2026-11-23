"""Úprava návrhu v kontrolní tabulce (ProposalEdited): R1 a R6."""

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.events import (
    MessageSent,
    ProposalConfirmed,
    ProposalEdited,
    ProposalReceived,
)
from decision_engine.core.model.proposal import ChangeProposal, PartDraft
from decision_engine.core.state import AppState, is_result_stale

pytestmark = pytest.mark.flow


def _edit(proposal: ChangeProposal, **changes: object) -> ProposalEdited:
    data = {
        "name": proposal.name,
        "material": proposal.material,
        "parts": proposal.parts,
        "stock": proposal.stock,
        "parameters": proposal.parameters,
    }
    return ProposalEdited.model_validate({**data, **changes})


def _with_proposal() -> AppState:
    state, _ = run([MessageSent(text="regál"), ProposalReceived(proposal=shelf_proposal())])
    assert state.proposal is not None
    return state


def test_zmenena_hodnota_prestane_byt_nepotvrzena() -> None:
    state = _with_proposal()
    proposal = state.proposal
    assert proposal is not None
    assert ("parameters", "kerf_mm") in proposal.unconfirmed

    edited = proposal.parameters.model_copy(update={"kerf_mm": 4})
    state, effects = run([_edit(proposal, parameters=edited)], state)

    assert effects == ()
    assert state.proposal is not None
    assert state.proposal.parameters.kerf_mm == 4
    assert ("parameters", "kerf_mm") not in state.proposal.unconfirmed


def test_nezmenena_nepotvrzena_hodnota_zustane_oznacena() -> None:
    state = _with_proposal()
    proposal = state.proposal
    assert proposal is not None

    state, _ = run([_edit(proposal, name="Jiný název")], state)

    assert state.proposal is not None
    assert ("parameters", "kerf_mm") in state.proposal.unconfirmed


def test_smazani_radku_nepomicha_oznaceni() -> None:
    state = _with_proposal()
    proposal = state.proposal
    assert proposal is not None
    marked = proposal.model_copy(
        update={"unconfirmed": frozenset({("problem", "parts", 1, "length_mm")})}
    )
    state = state.model_copy(update={"proposal": marked})

    # Smaže první řádek: díl p2 se posune na index 0 a jeho označení musí jít s ním.
    state, _ = run([_edit(marked, parts=marked.parts[1:])], state)

    assert state.proposal is not None
    assert state.proposal.unconfirmed == {("problem", "parts", 0, "length_mm")}


def test_uprava_nemeni_zakazku_ani_vysledek() -> None:
    state, effects = run(
        [
            MessageSent(text="regál"),
            ProposalReceived(proposal=shelf_proposal()),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)
    before = state
    state, _ = run(
        [MessageSent(text="úprava"), ProposalReceived(proposal=shelf_proposal(base_revision=0))],
        state,
    )
    proposal = state.proposal
    assert proposal is not None

    new_part = PartDraft(id="p3", name="příčka", length_mm=850, quantity=2)
    state, _ = run([_edit(proposal, parts=(*proposal.parts, new_part))], state)

    assert state.project == before.project
    assert state.result == before.result
    assert is_result_stale(state)


def test_upravena_hodnota_se_po_potvrzeni_pouzije() -> None:
    state = _with_proposal()
    proposal = state.proposal
    assert proposal is not None

    parts = (proposal.parts[0].model_copy(update={"length_mm": 1750}), *proposal.parts[1:])
    state, effects = run([_edit(proposal, parts=parts), ProposalConfirmed()], state)

    assert state.project is not None
    assert state.project.problem.parts[0].length_mm == 1750
    assert effects


def test_uprava_bez_navrhu_nic_nedela() -> None:
    state, _ = run([])
    proposal = shelf_proposal()

    new_state, effects = run([_edit(proposal)], state)

    assert new_state == state
    assert effects == ()
