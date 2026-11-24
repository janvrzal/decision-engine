"""Ukotvení čísel z výstupu modelu (pravidlo 8, #54): vymyšlené číslo je odhad AI."""

from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from decision_engine.core.extraction import ExtractionOutput, proposal_from_extraction
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.number_anchors import grounded_reply, numbers_in

ZADANI = "Udělej mi zábradlí: 3 sloupky po 1,2 m a madla po 240 cm. Tyče 6 m po 320 Kč."


def _output(**data: Any) -> ExtractionOutput:
    return ExtractionOutput.model_validate(
        {
            "parts": [
                {"name": "sloupek", "length_mm": 1200, "quantity": 3},
                {"name": "madlo", "length_mm": 2400, "quantity": 2},
            ],
            "stock": [{"length_mm": 6000, "price": "320"}],
            **data,
        }
    )


@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("1 250 mm", Decimal(1250)),
        ("2,5 m", Decimal("2.5")),
        ("dvanáct sloupků", Decimal(12)),
        ("po metru dvacet", Decimal("1.2")),
        ("dvacet pět kusů", Decimal(25)),
    ],
)
def test_cisla_ve_zprave(text: str, number: Decimal) -> None:
    assert number in numbers_in(text)


def test_cislo_ze_zpravy_v_jinych_jednotkach_ma_oporu() -> None:
    proposal = proposal_from_extraction(_output(), None, ZADANI)

    assert ("problem", "parts", 0, "length_mm") not in proposal.estimated
    assert ("problem", "parts", 1, "length_mm") not in proposal.estimated
    assert ("problem", "stock", 0, "price") not in proposal.estimated


def test_vymysleny_pocet_je_odhad_ai_i_bez_uncertain() -> None:
    # Případ z reportu (extraction-dev-04): model vrátil 23 kusů místo 3.
    output = _output(
        parts=[
            {"name": "sloupek", "length_mm": 1200, "quantity": 23},
            {"name": "madlo", "length_mm": 2400, "quantity": 2},
        ]
    )

    proposal = proposal_from_extraction(output, None, ZADANI)

    path = ("problem", "parts", 0, "quantity")
    assert path in proposal.estimated
    assert path in proposal.unconfirmed


def test_navazujici_zmena_smi_prevzit_cisla_ze_zakazky(project_data: dict[str, Any]) -> None:
    base = Project.model_validate(project_data)
    first = base.problem.parts[0]
    output = _output(
        parts=[{"ref": first.id, "name": first.name, "length_mm": first.length_mm, "quantity": 9}]
    )

    proposal = proposal_from_extraction(output, base, "Udělej jich 9.")

    assert ("problem", "parts", 0, "length_mm") not in proposal.estimated
    assert ("problem", "parts", 0, "quantity") not in proposal.estimated


def test_bez_zpravy_se_neukotvuje() -> None:
    assert proposal_from_extraction(_output(), None).estimated == frozenset()


def test_odpoved_s_cisly_z_navrhu_je_v_poradku() -> None:
    proposal = proposal_from_extraction(_output(), None, ZADANI)

    assert grounded_reply("Rozpoznal jsem 2 druhy dílů a tyče 6 m po 320 Kč.", proposal)
    assert not grounded_reply("Rozpoznal jsem 12 sloupků po 1 000 mm.", proposal)


@given(st.integers(min_value=1, max_value=99_999))
def test_kazda_delka_ze_zpravy_ma_oporu(length: int) -> None:
    output = _output(parts=[{"name": "díl", "length_mm": length, "quantity": 1}])

    proposal = proposal_from_extraction(output, None, f"Potřebuju 1 díl {length} mm.")

    assert ("problem", "parts", 0, "length_mm") not in proposal.estimated
