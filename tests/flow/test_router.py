"""Router v toku (UC-05, ADR-0012): podporované zadání do extrakce, jinak odpověď aplikace."""

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.effects import CallExtractor
from decision_engine.core.events import (
    MessageSent,
    ProposalConfirmed,
    ProposalReceived,
    RouteDecided,
)
from decision_engine.core.routing import (
    RESULT_QUESTION_TEXT,
    UNCLEAR_TEXT,
    UNSUPPORTED_TEXT,
    RouteOutcome,
    RoutingDecision,
)
from decision_engine.core.state import AppState

pytestmark = pytest.mark.flow


def _decision(outcome: RouteOutcome, **data: object) -> RouteDecided:
    return RouteDecided(
        decision=RoutingDecision.model_validate({"outcome": outcome, "router": "test", **data})
    )


def _planned() -> AppState:
    state, effects = run(
        [
            MessageSent(text="regál"),
            _decision(RouteOutcome.SUPPORTED, capability="cutting_1d"),
            ProposalReceived(proposal=shelf_proposal()),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)
    return state


def test_nejasne_zadani_se_dopta_a_nabidne_rucni_zadani() -> None:
    state, effects = run([MessageSent(text="Chci vyrobit skříň."), _decision(RouteOutcome.UNCLEAR)])

    assert effects == ()
    assert state.pending is None
    assert state.proposal is None
    reply = state.messages[-1]
    assert reply.text == UNCLEAR_TEXT
    assert reply.offer_manual


def test_doptavaci_otazka_od_routeru_ma_prednost() -> None:
    question = "Z jakých tyčí budete řezat?"

    state, _ = run(
        [MessageSent(text="Řežu sloupky."), _decision(RouteOutcome.UNCLEAR, question=question)]
    )

    assert state.messages[-1].text == question


def test_nepodporovane_zadani_nespusti_vypocet() -> None:
    state, effects = run(
        [MessageSent(text="Naskládej bedny do dodávky."), _decision(RouteOutcome.UNSUPPORTED)]
    )

    assert effects == ()
    assert state.messages[-1].text == UNSUPPORTED_TEXT
    assert state.messages[-1].offer_manual


def test_dotaz_na_cenu_odpovi_spocitanou_cenou_materialu() -> None:
    state, effects = run(
        [
            MessageSent(text="Kolik to bude stát?"),
            _decision(RouteOutcome.SUPPORTED, capability="cost_estimate"),
        ],
        _planned(),
    )

    assert effects == ()
    assert "Orientační cena materiálu podle plánu je" in state.messages[-1].text


def test_dotaz_k_planu_nevytvori_navrh() -> None:
    state, effects = run(
        [
            MessageSent(text="Proč je tam tolik odpadu?"),
            _decision(RouteOutcome.SUPPORTED, capability="cutting_1d", intent="result_question"),
        ],
        _planned(),
    )

    assert effects == ()
    assert state.proposal is None
    assert state.messages[-1].text == RESULT_QUESTION_TEXT


def test_zmena_zakazky_jde_do_extrakce_s_puvodni_zakazkou() -> None:
    before = _planned()
    _, effects = run(
        [
            MessageSent(text="Přidej 4 příčky po 850 mm."),
            _decision(RouteOutcome.SUPPORTED, capability="cutting_1d", intent="change_order"),
        ],
        before,
    )

    assert effects == (CallExtractor(text="Přidej 4 příčky po 850 mm.", base=before.project),)
