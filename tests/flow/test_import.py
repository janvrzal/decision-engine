"""Načtení souboru zakázky přes reducer (UC-06): nová zakázka jako návrh, chyba nic nezmění."""

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.events import (
    MessageSent,
    ProjectImported,
    ProposalConfirmed,
    ProposalReceived,
    SolveRequested,
)
from decision_engine.core.model.proposal import confirm_proposal
from decision_engine.core.project_file import write_project_file
from decision_engine.core.result import Ok
from decision_engine.core.state import AppState, Step, current_step

pytestmark = pytest.mark.flow


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


def _saved() -> str:
    match confirm_proposal(shelf_proposal(), "jina-relace", 3):
        case Ok(project):
            return write_project_file(project)
        case _:
            raise AssertionError("ukázková zakázka musí být platná")


def test_nacteni_zacne_novou_zakazku_ke_kontrole_bez_vypoctu() -> None:
    state, effects = run([ProjectImported(content=_saved())], _planned())

    assert effects == ()
    assert current_step(state) is Step.REVIEW
    assert state.project is None
    assert state.result is None
    assert state.proposal is not None
    assert state.proposal.origin == "file"
    assert [m.text for m in state.messages] == [
        "Zakázka načtena. Zkontrolujte údaje a spusťte výpočet."
    ]


def test_potvrzeni_nactene_zakazky_spocita_plan() -> None:
    state, effects = run([ProjectImported(content=_saved()), ProposalConfirmed()])
    state, _ = run([solved(effects)], state)

    assert state.project is not None
    assert state.project.revision == 0
    assert state.project.name == "Regál do dílny"
    assert state.result is not None


def test_neplatny_soubor_nic_nezmeni_a_chybu_dalsi_akce_schova() -> None:
    before = _planned()

    state, effects = run([ProjectImported(content="nesmysl")], before)

    assert effects == ()
    assert state.import_error == "Soubor není zakázka DecisionEngine."
    assert state.model_copy(update={"import_error": None}) == before

    state, _ = run([SolveRequested()], state)
    assert state.import_error is None


def test_behem_vypoctu_se_soubor_nenacte() -> None:
    state, _ = run([MessageSent(text="regál")])
    assert run([ProjectImported(content=_saved())], state) == (state, ())
