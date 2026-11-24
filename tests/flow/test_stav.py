"""Kritérium „Stav“ z kap. 9: změna vstupů nezanechá starý plán jako aktuální
a nepotvrzený ani neplatný návrh nepřepíše platnou zakázku."""

from collections.abc import Callable
from decimal import Decimal

import pytest
from scenario import run, shelf_proposal, solved

from decision_engine.core.events import (
    EditRequested,
    MessageSent,
    ProposalConfirmed,
    ProposalEdited,
    ProposalReceived,
    ProposalRejected,
)
from decision_engine.core.model.cutting_1d import Objective
from decision_engine.core.model.proposal import (
    ChangeProposal,
    PartDraft,
    StockLengthDraft,
)
from decision_engine.core.state import AppState, is_result_stale

pytestmark = pytest.mark.flow

Change = Callable[[ChangeProposal], ChangeProposal]


def _planned(objective: Objective = Objective.CHEAPEST) -> AppState:
    state, effects = run(
        [
            MessageSent(text="regál"),
            ProposalReceived(proposal=shelf_proposal(objective=objective)),
            ProposalConfirmed(),
        ]
    )
    state, _ = run([solved(effects)], state)
    assert not is_result_stale(state)
    return state


def _edit(proposal: ChangeProposal) -> ProposalEdited:
    return ProposalEdited(
        name=proposal.name,
        material=proposal.material,
        parts=proposal.parts,
        stock=proposal.stock,
        parameters=proposal.parameters,
    )


def _editing(state: AppState, change: Change) -> AppState:
    """„Upravit údaje“ a jedna změna v tabulce."""
    state, _ = run([EditRequested()], state)
    assert state.proposal is not None
    state, effects = run([_edit(change(state.proposal))], state)
    assert effects == ()
    return state


def _part(p: ChangeProposal, **update: object) -> ChangeProposal:
    return p.model_copy(update={"parts": (p.parts[0].model_copy(update=update), *p.parts[1:])})


def _stock(p: ChangeProposal, **update: object) -> ChangeProposal:
    return p.model_copy(update={"stock": (p.stock[0].model_copy(update=update), *p.stock[1:])})


def _parameter(p: ChangeProposal, **update: object) -> ChangeProposal:
    return p.model_copy(update={"parameters": p.parameters.model_copy(update=update)})


PLAN_INPUTS: dict[str, Change] = {
    "délka dílu": lambda p: _part(p, length_mm=1900),
    "počet dílů": lambda p: _part(p, quantity=5),
    "přidaný díl": lambda p: p.model_copy(
        update={"parts": (*p.parts, PartDraft(id="p3", name="vzpěra", length_mm=500, quantity=2))}
    ),
    "odebraný díl": lambda p: p.model_copy(update={"parts": p.parts[:1]}),
    "délka tyče": lambda p: _stock(p, length_mm=5000),
    "přidaná skladová délka": lambda p: p.model_copy(
        update={
            "stock": (
                *p.stock,
                StockLengthDraft(id="s2", length_mm=3000, price=Decimal("170.00")),
            )
        }
    ),
    "cena při nejnižší ceně": lambda p: _stock(p, price=Decimal("350.00")),
    "prořez": lambda p: _parameter(p, kerf_mm=4),
    "zarovnávací ořez": lambda p: _parameter(p, trim_mm=10),
    "minimální zbytek": lambda p: _parameter(p, min_remnant_mm=500),
    "časový limit": lambda p: _parameter(p, time_limit_s=3),
    "cíl": lambda p: _parameter(p, objective=Objective.FEWEST_BARS),
}


@pytest.mark.parametrize("change", PLAN_INPUTS.values(), ids=PLAN_INPUTS.keys())
def test_zmena_vstupu_planu_nezanecha_stary_plan_jako_aktualni(change: Change) -> None:
    before = _planned()

    editing = _editing(before, change)
    assert is_result_stale(editing)
    assert editing.project == before.project
    assert editing.result == before.result

    confirmed, effects = run([ProposalConfirmed()], editing)
    assert confirmed.project is not None
    assert confirmed.project.revision == 1
    assert is_result_stale(confirmed)  # starý plán, dokud nedoběhne výpočet nové revize

    solved_state, _ = run([solved(effects)], confirmed)
    assert solved_state.result is not None
    assert solved_state.result.source == solved_state.project
    assert not is_result_stale(solved_state)


OTHER_INPUTS: dict[str, tuple[Objective, Change]] = {
    "název": (Objective.CHEAPEST, lambda p: p.model_copy(update={"name": "Regál 2"})),
    "materiál": (Objective.CHEAPEST, lambda p: p.model_copy(update={"material": "jekl 30×30"})),
    "cena při jiném cíli": (
        Objective.FEWEST_BARS,
        lambda p: _stock(p, price=Decimal("350.00")),
    ),
}


@pytest.mark.parametrize(("objective", "change"), OTHER_INPUTS.values(), ids=OTHER_INPUTS.keys())
def test_zmena_mimo_vstupy_planu_plan_nezneplatni(objective: Objective, change: Change) -> None:
    before = _planned(objective)

    confirmed, _ = run([ProposalConfirmed()], _editing(before, change))

    assert confirmed.project is not None
    assert confirmed.project.revision == 1
    assert not is_result_stale(confirmed)


def test_neplatna_uprava_neprepise_potvrzenou_zakazku() -> None:
    before = _planned()
    editing = _editing(before, lambda p: _part(p, length_mm=-5))

    state, effects = run([ProposalConfirmed()], editing)

    assert effects == ()
    assert state.project == before.project
    assert state.result == before.result
    assert state.pending is None
    assert [e.path for e in state.proposal_errors] == [("problem", "parts", 0, "length_mm")]
    assert is_result_stale(state)  # návrh pořád čeká


def test_navrh_od_ai_nad_zakazkou_ji_nezmeni() -> None:
    before = _planned()

    state, effects = run(
        [
            MessageSent(text="Nohy ať jsou 2 m."),
            ProposalReceived(proposal=shelf_proposal(base_revision=0, shelf_length=2000)),
        ],
        before,
    )

    assert effects == ()
    assert state.project == before.project
    assert state.result == before.result
    assert is_result_stale(state)


def test_zahodit_zmeny_vrati_posledni_potvrzenou_revizi() -> None:
    before = _planned()
    state = _editing(before, lambda p: _part(p, length_mm=1900))
    assert state.proposal is not None
    state, _ = run([_edit(_parameter(state.proposal, kerf_mm=5))], state)

    state, effects = run([ProposalRejected()], state)

    assert effects == ()
    assert state.proposal is None
    assert state.project == before.project
    assert state.result == before.result
    assert not is_result_stale(state)
