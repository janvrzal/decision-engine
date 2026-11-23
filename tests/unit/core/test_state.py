"""Testy odvozených vlastností stavu relace (R3, F0)."""

from decision_engine.core.state import Step, current_step, initial_state, is_result_stale


def test_nova_relace_zacina_zadanim() -> None:
    state = initial_state("relace-1")

    assert current_step(state) is Step.INPUT
    assert state.project is None
    assert state.messages == ()


def test_bez_vysledku_neni_co_zneplatnit() -> None:
    assert not is_result_stale(initial_state("relace-1"))
