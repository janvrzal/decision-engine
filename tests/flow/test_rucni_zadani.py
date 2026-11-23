"""Ruční zadání bez AI (UC-13) a ruční úprava potvrzené zakázky („Upravit údaje“)."""

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.events import (
    EditRequested,
    MessageSent,
    ProposalConfirmed,
    ProposalEdited,
    ProposalReceived,
    ProposalRejected,
    ToolSelected,
)
from decision_engine.core.model.proposal import ChangeProposal
from decision_engine.core.state import AppState, Step, current_step, is_result_stale

pytestmark = pytest.mark.flow


def _filled(proposal: ChangeProposal) -> ProposalEdited:
    """Uživatel vyplní tabulku stejnými údaji, jaké by vrátila extrakce regálu."""
    shelf = shelf_proposal()
    return ProposalEdited(
        name=shelf.name,
        material=shelf.material,
        parts=shelf.parts,
        stock=shelf.stock,
        parameters=shelf.parameters,
    )


def _planned_by_ai() -> AppState:
    state, effects = run(
        [
            MessageSent(text="regál"),
            ProposalReceived(proposal=shelf_proposal()),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)
    return state


def test_volba_nastroje_otevre_prazdnou_kontrolu_bez_ai() -> None:
    state, effects = run([ToolSelected(capability="cutting_1d")])

    assert effects == ()
    assert current_step(state) is Step.REVIEW
    proposal = state.proposal
    assert proposal is not None
    assert proposal.origin == "manual"
    assert proposal.base_revision is None
    assert proposal.parts == ()
    assert ("parameters", "objective") in proposal.unconfirmed
    assert state.messages == ()


def test_rucni_cesta_da_stejny_plan_jako_cesta_pres_ai() -> None:
    state, _ = run([ToolSelected(capability="cutting_1d")])
    assert state.proposal is not None
    state, effects = run([_filled(state.proposal), ProposalConfirmed()], state)
    state, _ = run([solved(effects)], state)

    by_ai = _planned_by_ai()
    assert state.result is not None
    assert by_ai.result is not None
    assert state.result.bars == by_ai.result.bars
    assert state.result.metrics == by_ai.result.metrics


def test_volba_nastroje_nad_existujici_zakazkou_nic_nezmeni() -> None:
    state = _planned_by_ai()
    after, effects = run([ToolSelected(capability="cutting_1d")], state)
    assert (after, effects) == (state, ())


def test_upravit_udaje_nabidne_potvrzenou_zakazku_k_uprave() -> None:
    state = _planned_by_ai()
    assert state.project is not None

    state, effects = run([EditRequested()], state)

    assert effects == ()
    assert current_step(state) is Step.REVIEW
    proposal = state.proposal
    assert proposal is not None
    assert proposal.base_revision == 0
    assert proposal.unconfirmed == frozenset()
    assert [p.length_mm for p in proposal.parts] == [1800, 1200]
    # Čekající návrh označí plán jako neaktuální (R3), výsledek ale zůstává.
    assert state.result is not None
    assert is_result_stale(state)


def test_uprava_potvrzene_zakazky_vytvori_novou_revizi() -> None:
    state, _ = run([EditRequested()], _planned_by_ai())
    proposal = state.proposal
    assert proposal is not None
    longer = (proposal.parts[0].model_copy(update={"length_mm": 1900}), *proposal.parts[1:])
    edit = ProposalEdited(
        name=proposal.name,
        material=proposal.material,
        parts=longer,
        stock=proposal.stock,
        parameters=proposal.parameters,
    )

    state, effects = run([edit, ProposalConfirmed()], state)
    state, _ = run([solved(effects)], state)

    assert state.project is not None
    assert state.project.revision == 1
    assert state.project.problem.parts[0].length_mm == 1900
    assert not is_result_stale(state)


def test_zahozeni_upravy_vrati_aktualni_plan() -> None:
    state, _ = run([EditRequested(), ProposalRejected()], _planned_by_ai())
    assert state.proposal is None
    assert not is_result_stale(state)


@pytest.mark.parametrize("event", [ToolSelected(capability="cutting_1d"), EditRequested()])
def test_bez_odpovidajiciho_stavu_rucni_navrh_nevznikne(
    event: ToolSelected | EditRequested,
) -> None:
    # Během extrakce i bez zakázky (u úpravy) se stav nemění.
    pending, _ = run([MessageSent(text="regál")])
    assert run([event], pending) == (pending, ())
    if isinstance(event, EditRequested):
        empty, _ = run([])
        assert run([event], empty) == (empty, ())
