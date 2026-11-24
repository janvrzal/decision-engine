"""Nářezový plán 1D jako SVG (plan-rezani.md, varianta „Řezné značky“; ADR-0007).

Čistá funkce: stejné SVG zobrazí UI i PDF. Názvy dílů pocházejí od uživatele nebo
modelu, proto se každý text a atribut escapuje.
"""

from collections import Counter
from xml.sax.saxutils import escape, quoteattr

from decision_engine.core.model.calculation import Bar, CalculationResult
from decision_engine.core.model.cutting_1d import Parameters, Project
from decision_engine.core.render.format import bars_word, millimeters, number
from decision_engine.core.render.groups import BarGroup, group_bars
from decision_engine.core.render.plan_colors import PLAN_COLORS, part_color
from decision_engine.core.solvers.cutting_1d.geometry import remainder

WIDTH = 960
PAD = 16
GROUP_COLUMN = 72
BAR_HEIGHT = 26
CUT_AREA = 34
"""Místo nad tyčí pro dvě řady poloh řezů (svislý rozestup mezi tyčemi)."""
STRIPE = 5
TOP = 40
LEGEND_COLUMN = 224
LABEL_FULL_PX = 110
LABEL_SHORT_PX = 40
CUT_LABEL_GAP_PX = 48
CUT_ROW_PX = 14
FONT = "'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif"
C = PLAN_COLORS


def render_svg(result: CalculationResult) -> str:
    """Vykreslí plán výsledku do SVG."""
    project = result.source
    groups = group_bars(result)
    x0 = PAD + GROUP_COLUMN
    longest = max(stock.length_mm for stock in project.problem.stock)
    scale = (WIDTH - x0 - PAD) / longest

    body: list[str] = [_text(PAD, 20, _summary(project, result), 13, C["ink-muted"])]
    y = TOP
    for group in groups:
        body += _group(project, group, x0, y + CUT_AREA, scale)
        y += CUT_AREA + BAR_HEIGHT
    if not groups:
        body.append(_text(PAD, y + 20, "Žádná tyč", 14, C["ink-muted"]))
        y += 40
    legend, height = _legend(project, result, y + 24)
    body += legend

    kerf = millimeters(project.parameters.kerf_mm)
    title = f"Nářezový plán: {_bars_phrase(result)}, prořez {kerf}"
    return "".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" role="img" '
            f'aria-labelledby="plan-title plan-desc" font-family="{FONT}" '
            'style="font-variant-numeric: tabular-nums">',
            f'<title id="plan-title">{escape(title)}</title>',
            f'<desc id="plan-desc">{escape(_description(project, groups))}</desc>',
            "<defs>",
            '<pattern id="plan-hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)">',
            f'<rect width="6" height="6" fill="{C["plan-waste"]}"/>',
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="{C["plan-waste-hatch"]}" '
            'stroke-width="1"/>',
            "</pattern>",
            "</defs>",
            *body,
            "</svg>",
        ]
    )


def _group(project: Project, group: BarGroup, x0: float, y: float, scale: float) -> list[str]:
    bar = group.bar
    params = project.parameters
    names = {part.id: part.name for part in project.problem.parts}
    types = {part.id: index for index, part in enumerate(project.problem.parts)}
    out = [
        _text(PAD, y + 13, f"{group.count}×", 14, C["ink"], weight=600),
        _text(PAD, y + 25, group.label(), 11, C["ink-muted"]),
        f'<rect x="{_n(x0)}" y="{_n(y)}" width="{_n(bar.length_mm * scale)}" '
        f'height="{BAR_HEIGHT}" rx="2" fill="{C["plan-bar"]}" stroke="{C["border-strong"]}"/>',
    ]
    if params.trim_mm:
        trim = float(params.trim_mm) * scale
        out.append(_waste(x0, y, trim, f"ořez {millimeters(params.trim_mm)}"))
    for piece in bar.pieces:
        x = x0 + float(piece.start_mm) * scale
        width = piece.length_mm * scale
        name = names.get(piece.part_id, piece.part_id)
        tooltip = f"{name} {millimeters(piece.length_mm)}"
        label = (
            f"{name} {number(piece.length_mm)}"
            if width >= LABEL_FULL_PX
            else number(piece.length_mm)
            if width >= LABEL_SHORT_PX
            else ""
        )
        out.append(
            f"<g data-part-id={quoteattr(piece.part_id)}><title>{escape(tooltip)}</title>"
            f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{BAR_HEIGHT}" '
            f'fill="{C["surface"]}" stroke="{C["border-strong"]}"/>'
            f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{STRIPE}" '
            f'fill="{part_color(types.get(piece.part_id, 0))}"/>'
            + (_text(x + width / 2, y + 19, label, 11, C["ink"], anchor="middle") if label else "")
            + "</g>"
        )
    out += _cuts(bar, x0, y, scale)
    out += _tail(bar, params, x0, y, scale)
    return out


def _cuts(bar: Bar, x0: float, y: float, scale: float) -> list[str]:
    """Řezné značky na konci každého kusu, za kterým ještě je materiál."""
    out: list[str] = []
    last_in_row: list[float | None] = [None, None]
    for piece in bar.pieces:
        end = piece.start_mm + piece.length_mm
        if end >= bar.length_mm:
            continue
        x = x0 + float(end) * scale
        # Popisek do první řady, kde nepřekryje předchozí; jinak jen tooltip (poloha je
        # i v popisu SVG a v rozpisu po tyčích).
        row = next(
            (
                index
                for index, last in enumerate(last_in_row)
                if last is None or x - last >= CUT_LABEL_GAP_PX
            ),
            None,
        )
        label = ""
        if row is not None:
            last_in_row[row] = x
            label = _text(
                x,
                y - 9 - row * CUT_ROW_PX,
                number(end),
                11,
                C["plan-cut"],
                weight=600,
                anchor="middle",
            )
        out.append(
            f"<g><title>řez na {escape(millimeters(end))} od začátku tyče</title>"
            f'<line x1="{_n(x)}" y1="{_n(y)}" x2="{_n(x)}" y2="{_n(y + BAR_HEIGHT)}" '
            f'stroke="{C["plan-cut"]}" stroke-width="1.5"/>'
            f'<polygon points="{_n(x - 4)},{_n(y - 7)} {_n(x + 4)},{_n(y - 7)} '
            f'{_n(x)},{_n(y - 1)}" fill="{C["plan-cut"]}"/>' + label + "</g>"
        )
    return out


def _tail(bar: Bar, params: Parameters, x0: float, y: float, scale: float) -> list[str]:
    """Využitelný zbytek, nebo odpad za posledním kusem."""
    kind, length = remainder(bar.length_mm, bar.pieces, params)
    if kind == "none":
        return []
    start = bar.length_mm - length
    x, width = x0 + float(start) * scale, float(length) * scale
    if kind == "waste":
        return [_waste(x, y, width, f"odpad {millimeters(length)}")]
    label = f"zbytek {number(length)}"
    return [
        f"<g><title>využitelný zbytek {escape(millimeters(length))}</title>"
        f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{BAR_HEIGHT}" '
        f'fill="{C["plan-remnant"]}" stroke="{C["border-strong"]}"/>'
        + (
            _text(x + width / 2, y + 17, label, 11, C["success"], weight=600, anchor="middle")
            if width >= LABEL_FULL_PX * 0.7
            else ""
        )
        + "</g>"
    ]


def _waste(x: float, y: float, width: float, tooltip: str) -> str:
    return (
        f"<g><title>{escape(tooltip)}</title>"
        f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(width)}" height="{BAR_HEIGHT}" '
        f'fill="url(#plan-hatch)" stroke="{C["border-strong"]}"/></g>'
    )


def _legend(project: Project, result: CalculationResult, y: float) -> tuple[list[str], int]:
    placed = Counter(p.part_id for bar in result.bars for p in bar.pieces)
    entries: list[tuple[str, str]] = [
        (
            f'<rect width="12" height="12" fill="{C["surface"]}" stroke="{C["border-strong"]}"/>'
            f'<rect width="12" height="4" fill="{part_color(index)}"/>',
            _legend_part(part.name, part.length_mm, placed[part.id], part.quantity),
        )
        for index, part in enumerate(project.problem.parts)
    ]
    entries += [
        (
            f'<line x1="6" y1="0" x2="6" y2="12" stroke="{C["plan-cut"]}" stroke-width="1.5"/>',
            "řez, číslo = poloha od začátku tyče",
        ),
        (
            f'<rect width="12" height="12" fill="{C["plan-remnant"]}" '
            f'stroke="{C["border-strong"]}"/>',
            f"využitelný zbytek od {millimeters(project.parameters.min_remnant_mm)}",
        ),
        (
            f'<rect width="12" height="12" fill="url(#plan-hatch)" stroke="{C["border-strong"]}"/>',
            "odpad",
        ),
    ]
    per_row = (WIDTH - 2 * PAD) // LEGEND_COLUMN
    out: list[str] = []
    for index, (swatch, text) in enumerate(entries):
        x = PAD + (index % per_row) * LEGEND_COLUMN
        row_y = y + (index // per_row) * 22
        out.append(f'<g transform="translate({_n(x)},{_n(row_y)})">{swatch}</g>')
        out.append(_text(x + 18, row_y + 10, text, 12, C["ink"]))
    rows = (len(entries) + per_row - 1) // per_row
    return out, int(y + rows * 22 + PAD)


def _legend_part(name: str, length_mm: int, placed: int, quantity: int) -> str:
    base = f"{name} {millimeters(length_mm)}"
    if placed == quantity:
        return f"{base} ({quantity}×)"
    return f"{base} (umístěno {placed} z {quantity})"


def _summary(project: Project, result: CalculationResult) -> str:
    parts = [_bars_phrase(result), f"prořez {millimeters(project.parameters.kerf_mm)}"]
    if project.parameters.trim_mm:
        parts.append(f"ořez {millimeters(project.parameters.trim_mm)}")
    parts.append("polohy řezů od začátku tyče")
    return " · ".join(parts)


def _bars_phrase(result: CalculationResult) -> str:
    """„5 tyčí po 6 000 mm“, u více délek „3 tyče po 6 000 mm a 2 tyče po 4 000 mm“."""
    counts = Counter(bar.length_mm for bar in result.bars)
    if not counts:
        return "žádná tyč"
    phrases = [
        f"{count} {bars_word(count)} po {millimeters(length)}"
        for length, count in sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    ]
    return ", ".join(phrases[:-1]) + " a " + phrases[-1] if len(phrases) > 1 else phrases[0]


def _description(project: Project, groups: tuple[BarGroup, ...]) -> str:
    names = {part.id: part.name for part in project.problem.parts}
    lines: list[str] = []
    for group in groups:
        bar = group.bar
        pieces = ", ".join(
            f"{names.get(p.part_id, p.part_id)} {number(p.length_mm)}" for p in bar.pieces
        )
        cuts = [
            number(p.start_mm + p.length_mm)
            for p in bar.pieces
            if p.start_mm + p.length_mm < bar.length_mm
        ]
        kind, length = remainder(bar.length_mm, bar.pieces, project.parameters)
        tail = {"remnant": f"zbytek {millimeters(length)}", "waste": f"odpad {millimeters(length)}"}
        text = f"{group.count}× tyč {millimeters(bar.length_mm)} ({group.label()}): {pieces}"
        if cuts:
            text += f"; řezy na {', '.join(cuts)}"
        if kind in tail:
            text += f"; {tail[kind]}"
        lines.append(text + ".")
    return " ".join(lines) if lines else "Plán neobsahuje žádnou tyč."


def _text(
    x: float,
    y: float,
    content: str,
    size: int,
    fill: str,
    *,
    weight: int = 400,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{_n(x)}" y="{_n(y)}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{escape(content)}</text>'
    )


def _n(value: float) -> str:
    """Souřadnice zaokrouhlená na setiny bez zbytečných nul (stabilní snapshoty)."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text
