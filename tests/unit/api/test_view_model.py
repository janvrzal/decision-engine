"""Jednotkové testy sestavení view modelu: popisky chyb, důvody a stavy kroků."""

import pytest

from decision_engine.api.view_builder import build_view_model
from decision_engine.api.view_proposal import confirm_disabled_reason, field_label, field_target
from decision_engine.core.errors import FieldPath
from decision_engine.core.state import Message, PendingOperation, initial_state


@pytest.mark.parametrize(
    ("path", "label"),
    [
        (("problem", "parts", 1, "length_mm"), "Díl 2, délka"),
        (("problem", "stock", 0, "price"), "Skladová délka 1, cena"),
        (("problem", "parts"), "Díly"),
        (("parameters", "kerf_mm"), "Prořez"),
        (("name",), "Název"),
        ((), "Zakázka"),
    ],
)
def test_citelne_umisteni_chyby(path: FieldPath, label: str) -> None:
    assert field_label(path) == label


@pytest.mark.parametrize(
    ("path", "target"),
    [
        (("problem", "parts", 1, "length_mm"), "parts.1.length_mm"),
        (("problem", "stock", 0, "price"), "stock.0.price"),
        (("problem", "parts", 2, "id"), "parts.2.name"),
        (("problem", "stock", 0, "id"), "stock.0.length_mm"),
        (("problem", "stock"), "stock"),
        (("parameters", "kerf_mm"), "parameters.kerf_mm"),
        (("parameters", "objective"), "parameters.objective"),
        (("name",), "name"),
        (("parameters", "neznamy"), None),
        ((), None),
    ],
)
def test_odkaz_chyby_na_pole(path: FieldPath, target: str | None) -> None:
    assert field_target(path) == target


@pytest.mark.parametrize(
    ("count", "text"),
    [
        (0, None),
        (1, "Opravte 1 pole, než spustíte výpočet."),
        (3, "Opravte 3 pole, než spustíte výpočet."),
        (5, "Opravte 5 polí, než spustíte výpočet."),
    ],
)
def test_duvod_neaktivniho_potvrzeni(count: int, text: str | None) -> None:
    assert confirm_disabled_reason(count) == text


def test_nova_relace() -> None:
    view = build_view_model(initial_state("r"), extraction_available=False)

    assert view.session.ai.extraction_available is False
    assert [s.state for s in view.project.steps] == ["active", "unavailable", "unavailable"]
    assert view.project.has_content is False
    assert view.proposal is None
    assert view.result is None


def test_bezici_extrakce_ma_popisek() -> None:
    state = initial_state("r").model_copy(
        update={
            "pending": PendingOperation(kind="extraction"),
            "messages": (Message(id=1, role="user", kind="text", text="ahoj"),),
        }
    )

    view = build_view_model(state, extraction_available=True)

    assert view.pending_operation is not None
    assert view.pending_operation.label == "Připravuji údaje ke kontrole…"
    assert view.project.has_content is True


def test_neznamy_druh_chyby_ma_obecny_text() -> None:
    state = initial_state("r").model_copy(
        update={"messages": (Message(id=1, role="assistant", kind="error"),)}
    )

    view = build_view_model(state, extraction_available=True)

    assert view.messages[0].text.startswith("AI teď neodpovídá")
