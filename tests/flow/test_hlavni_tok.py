"""Hlavní tok zakázky přes reducer: sled událostí → očekávaný stav (ADR-0006, F0, R1, R3)."""

from decimal import Decimal

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.effects import CallExtractor, CallRouter, RunSolver
from decision_engine.core.events import (
    AiFailed,
    MessageSent,
    ProposalConfirmed,
    ProposalReceived,
    ProposalRejected,
    RouteDecided,
    SolveRequested,
)
from decision_engine.core.model.cutting_1d import Objective
from decision_engine.core.routing import NO_ORDER, RouteOutcome, RoutingDecision
from decision_engine.core.state import AppState, Step, current_step, is_result_stale

pytestmark = pytest.mark.flow

ZADANI = "Regál: 4 nohy po 1 800 mm a 8 polic po 1 200 mm z tyčí 6 m."


def _planned() -> AppState:
    """Zakázka s potvrzenou revizí 0 a aktuálním plánem."""
    state, effects = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal(), reply="Připravil jsem údaje."),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)
    return state


SUPPORTED = RoutingDecision(outcome=RouteOutcome.SUPPORTED, capability="cutting_1d", router="test")


def test_uc01_od_zpravy_k_planu() -> None:
    state, effects = run([MessageSent(text=ZADANI)])
    # Nejdřív router (ADR-0012), u podporovaného zadání pak extrakce.
    assert effects == (CallRouter(text=ZADANI, order={"rozpracovana_zakazka": NO_ORDER}),)
    assert state.pending is not None
    assert state.pending.kind == "extraction"
    state, effects = run([RouteDecided(decision=SUPPORTED)], state)
    assert effects == (CallExtractor(text=ZADANI, base=None),)

    state, effects = run([ProposalReceived(proposal=shelf_proposal())], state)
    assert effects == ()
    assert current_step(state) is Step.REVIEW
    assert state.project is None

    state, effects = run([ProposalConfirmed()], state)
    assert state.project is not None
    assert state.project.revision == 0
    assert state.proposal is None
    assert effects == (RunSolver(project=state.project),)

    state, _ = run([solved(effects)], state)
    assert state.result is not None
    assert state.pending is None
    assert current_step(state) is Step.RESULT
    assert not is_result_stale(state)


def test_nepotvrzeny_navrh_neprepise_data() -> None:
    before = _planned()

    state, _ = run(
        [
            MessageSent(text="Poličky ať jsou 1 250 mm."),
            ProposalReceived(proposal=shelf_proposal(base_revision=0, shelf_length=1250)),
        ],
        before,
    )

    assert state.project == before.project
    assert state.result == before.result
    assert is_result_stale(state)
    assert current_step(state) is Step.REVIEW

    state, _ = run([ProposalRejected()], state)
    assert state.project == before.project
    assert not is_result_stale(state)
    assert current_step(state) is Step.RESULT


def test_uprava_vytvori_novou_revizi_a_prepocet() -> None:
    before = _planned()
    state, effects = run(
        [
            MessageSent(text="Poličky ať jsou 1 250 mm."),
            ProposalReceived(proposal=shelf_proposal(base_revision=0, shelf_length=1250)),
            ProposalConfirmed(),
        ],
        before,
    )

    assert state.project is not None
    assert state.project.revision == 1
    assert state.project.problem.parts[1].length_mm == 1250
    assert is_result_stale(state)  # starý plán, dokud nedoběhne výpočet

    state, _ = run([solved(effects)], state)
    assert not is_result_stale(state)


def test_neplatny_navrh_nespusti_vypocet() -> None:
    state, effects = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal(shelf_length=None)),
            ProposalConfirmed(),
        ]
    )

    assert effects == ()
    assert state.project is None
    assert state.proposal is not None
    assert [e.path for e in state.proposal_errors] == [("problem", "parts", 1, "length_mm")]
    assert state.proposal_errors[0].message == "Chybí hodnota."


def test_nejnizsi_cena_bez_ceny_nespusti_vypocet() -> None:
    state, effects = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal(price=None)),
            ProposalConfirmed(),
        ]
    )

    assert effects == ()
    assert state.proposal_errors[0].code == "missing_price"


def test_novy_navrh_smaze_stare_chyby() -> None:
    state, _ = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal(shelf_length=None)),
            ProposalConfirmed(),
            ProposalRejected(),
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal()),
        ]
    )

    assert state.proposal_errors == ()


def test_vypadek_ai_nezmeni_data_a_dovoli_dalsi_zpravu() -> None:
    before = _planned()

    state, _ = run([MessageSent(text="Přidej příčku."), AiFailed(kind="connection")], before)

    assert state.project == before.project
    assert state.result == before.result
    assert state.pending is None
    assert state.messages[-1].kind == "error"
    assert state.messages[-1].error_kind == "connection"
    # „Zkusit znovu“ pošle tutéž zprávu i po obnovení stránky (text je ve stavu).
    assert state.messages[-1].retry_text == "Přidej příčku."

    _, effects = run([MessageSent(text="Přidej příčku.")], state)
    assert isinstance(effects[0], CallRouter)


def test_zprava_behem_operace_se_ignoruje() -> None:
    state, _ = run([MessageSent(text=ZADANI)])

    again, effects = run([MessageSent(text="ještě jednou")], state)

    assert effects == ()
    assert again == state


def test_prazdna_zprava_se_ignoruje() -> None:
    state, effects = run([MessageSent(text="   ")])

    assert effects == ()
    assert state.messages == ()


def test_opozdeny_vysledek_stare_revize_se_ignoruje() -> None:
    state, first = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal()),
            ProposalConfirmed(),
        ]
    )
    old_result = solved(first)
    state, _ = run([old_result], state)
    state, second = run(
        [
            MessageSent(text="Poličky 1 250 mm."),
            ProposalReceived(proposal=shelf_proposal(base_revision=0, shelf_length=1250)),
            ProposalConfirmed(),
        ],
        state,
    )

    late, _ = run([old_result], state)

    assert late.pending is not None
    assert late.result == state.result
    assert late == state
    assert second  # nový výpočet stále běží


def test_prepocitat_spusti_vypocet_aktualni_revize() -> None:
    state, effects = run([SolveRequested()], _planned())

    assert state.project is not None
    assert effects == (RunSolver(project=state.project),)


def test_prepocitat_bez_zakazky_nic_nedela() -> None:
    state, effects = run([SolveRequested()])

    assert effects == ()
    assert state.pending is None


@pytest.mark.parametrize(
    ("objective", "stale"),
    [(Objective.LEAST_MATERIAL, False), (Objective.CHEAPEST, True)],
)
def test_zmena_ceny_zneplatni_plan_jen_pri_nejnizsi_cene(objective: Objective, stale: bool) -> None:
    state, effects = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal(objective=objective)),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)

    state, _ = run(
        [
            MessageSent(text="Tyč stojí 350 Kč."),
            ProposalReceived(
                proposal=shelf_proposal(0, price=Decimal("350.00"), objective=objective)
            ),
            ProposalConfirmed(),
        ],
        state,
    )

    assert state.project is not None
    assert state.project.revision == 1
    assert is_result_stale(state) is stale


def test_id_zprav_jsou_deterministicka() -> None:
    state, _ = run(
        [
            MessageSent(text=ZADANI),
            ProposalReceived(proposal=shelf_proposal(), reply="Připravil jsem údaje."),
        ]
    )

    assert [(m.id, m.role) for m in state.messages] == [(1, "user"), (2, "assistant")]


def test_udalost_bez_smyslu_stav_nezmeni() -> None:
    state, effects = run([ProposalConfirmed(), ProposalRejected(), AiFailed(kind="rate_limit")])

    assert effects == ()
    assert state == run([])[0]
