"""SVG plánu 1D: struktura, přístupnost, popisky, escapování a snapshoty (plan-rezani.md)."""

import itertools
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from solver_cases import project_1d

from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.render.samples import SAMPLES
from decision_engine.core.render.svg_1d import render_svg
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd

NS = {"svg": "http://www.w3.org/2000/svg"}
NBSP = "\u00a0"
SNAPSHOTS = Path(__file__).parent / "snapshots"


def _svg(project: Project) -> ET.Element:
    return ET.fromstring(render_svg(solve_ffd(project)))


def _texts(root: ET.Element) -> list[str]:
    return [t.text or "" for t in root.iterfind(".//svg:text", NS)]


def _num(text: str) -> str:
    """Zápis s běžnými mezerami → mezery jako v SVG (tisíce a před „mm“ nezlomitelné)."""
    return re.sub(r"(?<=\d) (?=\d{3}\b)|(?<=\d) (?=mm\b)", NBSP, text)


def test_pristupnost_role_title_desc() -> None:
    root = _svg(SAMPLES["jekly-a-pricky"])

    assert root.get("role") == "img"
    assert root.get("aria-labelledby") == "plan-title plan-desc"
    title = root.findtext("svg:title", namespaces=NS)
    assert title == _num("Nářezový plán: 5 tyčí po 6 000 mm, prořez 3 mm")
    desc = root.findtext("svg:desc", namespaces=NS) or ""
    assert _num("řezy na 2 000, 4 003, 5 506") in desc
    assert _num("zbytek 491 mm") in desc


def test_stejne_tyce_jsou_jedna_skupina() -> None:
    texts = _texts(_svg(SAMPLES["jekly-a-pricky"]))

    assert "5×" in texts
    assert "Tyč 1–5" in texts
    assert _num("5 tyčí po 6 000 mm · prořez 3 mm · polohy řezů od začátku tyče") in texts


def test_polohy_rezu_od_zacatku_tyce() -> None:
    texts = _texts(_svg(SAMPLES["jekly-a-pricky"]))

    for position in ("2 000", "4 003", "5 506"):
        assert _num(position) in texts


def test_kus_na_celou_delku_tyce_nema_rez_na_konci() -> None:
    root = _svg(project_1d([(6000, 1)], [(6000, None)], kerf=3))

    titles = [t.text or "" for t in root.iterfind(".//svg:g/svg:title", NS)]
    assert not [title for title in titles if title.startswith("řez na")]


def test_vyuzitelny_zbytek_a_odpad() -> None:
    remnant = _texts(_svg(project_1d([(700, 1)], [(1000, None)], min_remnant=300)))
    waste = render_svg(solve_ffd(project_1d([(701, 1)], [(1000, None)], min_remnant=300)))

    assert _num("zbytek 300") in remnant
    assert "url(#plan-hatch)" in waste
    assert _num("odpad 299 mm") in waste


def test_popisek_dilu_podle_sirky() -> None:
    project = project_1d([(3000, 1), (400, 1), (60, 1)], [(6000, None)])

    texts = _texts(_svg(project))

    assert _num("díl 1 3 000") in texts  # široký díl: název a délka
    assert "400" in texts  # užší díl: jen délka
    assert "60" not in texts  # velmi úzký díl: jen tooltip
    assert _num("díl 3 60 mm") in render_svg(solve_ffd(project))


def test_husté_rezy_nemaji_prekryvajici_popisky() -> None:
    root = _svg(project_1d([(50, 30)], [(6000, None)], kerf=3))

    rows: dict[str, list[float]] = {}
    for text in root.iterfind(".//svg:text[@fill='#a14f06']", NS):
        rows.setdefault(text.get("y", ""), []).append(float(text.get("x", "0")))
    for xs in rows.values():
        assert all(b - a >= 48 for a, b in itertools.pairwise(xs))


def test_legenda_s_prahem_a_neumistenymi_kusy() -> None:
    texts = _texts(_svg(SAMPLES["castecny"]))

    assert _num("využitelný zbytek od 300 mm") in texts
    assert _num("nosník 6 500 mm (umístěno 0 z 1)") in texts
    assert _num("sloupek 2 400 mm (3×)") in texts


def test_kazdy_kus_ma_data_part_id() -> None:
    result = solve_ffd(SAMPLES["regal-vice-delek"])
    root = ET.fromstring(render_svg(result))

    ids = [g.get("data-part-id") for g in root.iterfind(".//svg:g[@data-part-id]", NS)]
    unique_bars = {
        (b.stock_id, tuple((p.part_id, p.start_mm) for p in b.pieces)) for b in result.bars
    }
    assert len(ids) == sum(len(pieces) for _, pieces in unique_bars)


def test_barva_typu_se_opakuje_od_devateho_dilu() -> None:
    svg = render_svg(solve_ffd(SAMPLES["regal-vice-delek"]))

    # 9 typů dílů, 8 barev: devátý typ má barvu prvního.
    assert svg.count('fill="#9fc4e8"') >= 2


def test_nazev_dilu_se_escapuje() -> None:
    project = project_1d([(3000, 1)], [(6000, None)])
    parts = (project.problem.parts[0].model_copy(update={"name": '<script>alert("x")</script>'}),)
    project = project.model_copy(
        update={"problem": project.problem.model_copy(update={"parts": parts})}
    )

    svg = render_svg(solve_ffd(project))

    assert "<script>" not in svg
    ET.fromstring(svg)  # stále platné XML


def test_bez_reseni_vykresli_prazdny_plan() -> None:
    root = _svg(project_1d([(7000, 1)], [(6000, None)]))

    assert "Žádná tyč" in _texts(root)
    assert root.findtext("svg:title", namespaces=NS) == _num(
        "Nářezový plán: žádná tyč, prořez 0 mm"
    )


def test_vystup_je_deterministicky() -> None:
    result = solve_ffd(SAMPLES["regal-vice-delek"])

    assert render_svg(result) == render_svg(result)


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_snapshot(name: str) -> None:
    # Koncový řádek: soubor tak projde hookem end-of-file-fixer beze změny.
    svg = render_svg(solve_ffd(SAMPLES[name])) + "\n"
    path = SNAPSHOTS / f"{name}.svg"
    if os.environ.get("UPDATE_SNAPSHOTS") == "1" or not path.exists():
        path.parent.mkdir(exist_ok=True)
        path.write_text(svg, encoding="utf-8")
        pytest.skip(f"snapshot {path.name} zapsán")
    assert svg == path.read_text(encoding="utf-8"), (
        "SVG se změnilo; po kontrole spusťte UPDATE_SNAPSHOTS=1 uv run pytest"
    )
