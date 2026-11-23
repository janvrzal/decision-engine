"""Vlastnosti reduceru: žádná výjimka a zakázku mění jen potvrzení návrhu (R1)."""

from hypothesis import given
from hypothesis import strategies as st

from decision_engine.core.effects import RunSolver
from decision_engine.core.events import (
    AiFailed,
    Event,
    MessageSent,
    ProposalConfirmed,
    ProposalReceived,
    ProposalRejected,
    SolveFinished,
    SolveRequested,
)
from decision_engine.core.model.cutting_1d import Objective
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)
from decision_engine.core.reducer import reduce
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd
from decision_engine.core.state import initial_state


def _proposal(length: int | None) -> ChangeProposal:
    return ChangeProposal(
        base_revision=None,
        name="Zakázka",
        parts=(PartDraft(id="p1", name="díl", length_mm=length, quantity=2),),
        stock=(StockLengthDraft(id="s1", length_mm=6000),),
        parameters=ParametersDraft(
            kerf_mm=3, trim_mm=0, min_remnant_mm=0, objective=Objective.FEWEST_BARS
        ),
    )


_SOLVE_RESULT = object()
"""Zástupce: v toku se nahradí výsledkem posledního `RunSolver`."""

_events = st.lists(
    st.one_of(
        st.builds(MessageSent, text=st.text(max_size=10)),
        st.builds(
            ProposalReceived,
            proposal=st.builds(_proposal, st.none() | st.integers(1, 7000)),
        ),
        st.just(ProposalConfirmed()),
        st.just(ProposalRejected()),
        st.just(SolveRequested()),
        st.builds(AiFailed, kind=st.sampled_from(["connection", "rate_limit", "invalid_response"])),
        st.just(_SOLVE_RESULT),
    ),
    max_size=25,
)


@given(_events)
def test_libovolna_posloupnost_nevyhodi_vyjimku_a_zakazku_meni_jen_potvrzeni(
    steps: list[object],
) -> None:
    state = initial_state("relace")
    last_solver: RunSolver | None = None
    for step in steps:
        event: Event
        if step is _SOLVE_RESULT:
            if last_solver is None:
                continue
            event = SolveFinished(result=solve_ffd(last_solver.project))
        else:
            assert isinstance(
                step,
                MessageSent
                | ProposalReceived
                | ProposalConfirmed
                | ProposalRejected
                | SolveRequested
                | AiFailed,
            )
            event = step

        new_state, effects = reduce(state, event)

        if new_state.project != state.project:
            assert isinstance(event, ProposalConfirmed)
            assert new_state.project is not None
            expected = 0 if state.project is None else state.project.revision + 1
            assert new_state.project.revision == expected
        for effect in effects:
            if isinstance(effect, RunSolver):
                last_solver = effect
        state = new_state
