"""Nová zakázka a neuložené změny (UC-15, UC-06 A1): co by se zahozením ztratilo."""

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.events import (
    EditRequested,
    Event,
    MessageSent,
    NewProjectRequested,
    ProjectImported,
    ProjectSaved,
    ProposalConfirmed,
    ProposalEdited,
    ProposalReceived,
    ProposalRejected,
    ToolSelected,
)
from decision_engine.core.model.proposal import ChangeProposal, PartDraft, confirm_proposal
from decision_engine.core.project_file import write_project_file
from decision_engine.core.result import Ok
from decision_engine.core.state import AppState, Step, current_step, has_unsaved_changes

pytestmark = pytest.mark.flow


def _edit(proposal: ChangeProposal, **changes: object) -> ProposalEdited:
    values = {
        "name": proposal.name,
        "material": proposal.material,
        "parts": proposal.parts,
        "stock": proposal.stock,
        "parameters": proposal.parameters,
        **changes,
    }
    return ProposalEdited.model_validate(values)


def _planned() -> AppState:
    state, effects = run(
        [
            MessageSent(text="regál"),
            ProposalReceived(proposal=shelf_proposal()),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)
    return state


def _file() -> str:
    match confirm_proposal(shelf_proposal(), "jina-relace", 3):
        case Ok(project):
            return write_project_file(project)
        case _:
            raise AssertionError("ukázková zakázka musí být platná")


def _after(events: list[Event], state: AppState | None = None) -> AppState:
    return run(events, state)[0]


def test_prazdna_relace_nema_neulozene_zmeny() -> None:
    assert not has_unsaved_changes(_after([]))


def test_potvrzena_neulozena_zakazka_ma_neulozene_zmeny() -> None:
    assert has_unsaved_changes(_planned())


def test_ulozeni_aktualni_revize_zmeny_vyresi() -> None:
    state = _after([ProjectSaved(revision=0)], _planned())
    assert not has_unsaved_changes(state)


def test_ulozeni_jine_revize_nic_neoznaci() -> None:
    before = _planned()
    assert _after([ProjectSaved(revision=7)], before) == before


def test_zmena_ulozene_zakazky_je_neulozena() -> None:
    saved = _after([ProjectSaved(revision=0)], _planned())
    proposal = shelf_proposal()
    parts = (PartDraft(id="p1", name="noha", length_mm=1700, quantity=4),)
    events: list[Event] = [EditRequested(), _edit(proposal, parts=parts), ProposalConfirmed()]
    state, effects = run(events, saved)
    state, _ = run([solved(effects)], state)

    assert state.project is not None
    assert state.project.revision == 1
    assert has_unsaved_changes(state)


def test_netknuty_rucni_formular_neni_rozpracovana_prace() -> None:
    state = _after([ToolSelected(capability="cutting_1d")])
    assert state.proposal is not None
    assert not has_unsaved_changes(state)


def test_upraveny_rucni_formular_je_rozpracovana_prace() -> None:
    state = _after([ToolSelected(capability="cutting_1d")])
    assert state.proposal is not None
    state = _after([_edit(state.proposal, name="Plot")], state)
    assert has_unsaved_changes(state)


def test_upravit_udaje_bez_zmeny_ulozenou_zakazku_nezmeni() -> None:
    saved = _after([ProjectSaved(revision=0)], _planned())
    assert not has_unsaved_changes(_after([EditRequested()], saved))


def test_zahozeny_navrh_uz_neni_rozpracovany() -> None:
    saved = _after([ProjectSaved(revision=0)], _planned())
    proposal = shelf_proposal()
    state = _after([EditRequested(), _edit(proposal, name="Jiný"), ProposalRejected()], saved)
    assert not has_unsaved_changes(state)


def test_navrh_od_ai_je_rozpracovana_prace() -> None:
    state = _after([MessageSent(text="regál"), ProposalReceived(proposal=shelf_proposal())])
    assert has_unsaved_changes(state)


def test_nactena_a_potvrzena_zakazka_beze_zmen_je_ulozena() -> None:
    state = _after([ProjectImported(content=_file())])
    assert has_unsaved_changes(state)  # návrh ke kontrole ještě čeká

    state, effects = run([ProposalConfirmed()], state)
    state, _ = run([solved(effects)], state)
    assert not has_unsaved_changes(state)


def test_nova_zakazka_zacne_s_prazdnym_kontextem() -> None:
    before = _planned()
    state, effects = run([NewProjectRequested()], before)

    assert effects == ()
    assert state == AppState(session_id=before.session_id)
    assert current_step(state) is Step.INPUT


def test_nova_zakazka_zahodi_i_rozpracovany_navrh() -> None:
    state = _after([EditRequested(), NewProjectRequested()], _planned())
    assert state.proposal is None
    assert state.project is None
    assert not has_unsaved_changes(state)


def test_behem_operace_nova_zakazka_nic_nezmeni() -> None:
    state = _after([MessageSent(text="regál")])
    assert run([NewProjectRequested()], state) == (state, ())
