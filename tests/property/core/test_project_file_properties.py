"""Vlastnosti souboru zakázky: round-trip a žádná výjimka pro libovolný obsah."""

from hypothesis import given, settings
from hypothesis import strategies as st
from test_cutting_1d_properties import projects

from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.model.proposal import confirm_proposal
from decision_engine.core.project_file import read_project_file, write_project_file
from decision_engine.core.result import Err, Ok


@settings(max_examples=200)
@given(projects())
def test_ulozeni_a_nacteni_zachova_vstupy(project: Project) -> None:
    match read_project_file(write_project_file(project)):
        case Ok(proposal):
            assert confirm_proposal(proposal, project.id, project.revision) == Ok(project)
        case Err(message):
            raise AssertionError(message)


@given(st.text())
def test_libovolny_text_vrati_vysledek_a_nevyhodi_vyjimku(content: str) -> None:
    assert isinstance(read_project_file(content), Ok | Err)
