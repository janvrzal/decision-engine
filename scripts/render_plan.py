"""Vykreslí ukázkové plány do `build/plans/` pro vizuální kontrolu SVG (#13).

uv run python scripts/render_plan.py
"""

from pathlib import Path

from decision_engine.core.render.samples import SAMPLES
from decision_engine.core.render.svg_1d import render_svg
from decision_engine.core.solvers.cutting_1d.ffd import solve_ffd

OUT = Path(__file__).resolve().parents[1] / "build" / "plans"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, project in SAMPLES.items():
        path = OUT / f"{name}.svg"
        path.write_text(render_svg(solve_ffd(project)), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
