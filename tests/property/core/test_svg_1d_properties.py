"""SVG plánu je pro libovolnou platnou zakázku platné XML s každým kusem."""

import xml.etree.ElementTree as ET

from hypothesis import given, settings
from test_ffd_1d_properties import projects

from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.render.svg_1d import render_svg
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd

NS = {"svg": "http://www.w3.org/2000/svg"}


@settings(max_examples=100, deadline=None)
@given(projects())
def test_svg_je_platne_a_obsahuje_kazdy_typ_umisteneho_dilu(project: Project) -> None:
    result = solve_ffd(project)

    root = ET.fromstring(render_svg(result))

    drawn = {g.get("data-part-id") for g in root.iterfind(".//svg:g[@data-part-id]", NS)}
    placed = {p.part_id for bar in result.bars for p in bar.pieces}
    assert drawn == placed
    assert root.findtext("svg:title", namespaces=NS)
