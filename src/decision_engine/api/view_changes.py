"""Souhrn změn návrhu oproti potvrzené revizi (spec kap. 4, komponenty.md ChangeSummary)."""

from decimal import Decimal

from decision_engine.api.view_model import ChangesView, RemovedPartView, RemovedStockView
from decision_engine.core.errors import FieldPath
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import ChangeProposal
from decision_engine.core.model.proposal_diff import FieldChange, ProposalDiff, Value
from decision_engine.core.render.format import NBSP, millimeters, number

OBJECTIVE_LABEL = {
    Objective.CHEAPEST: "Nejnižší cena",
    Objective.FEWEST_BARS: "Nejméně tyčí",
    Objective.LEAST_MATERIAL: "Nejméně materiálu",
}
PARAMETER_LABEL = {
    "kerf_mm": "Prořez",
    "trim_mm": "Zarovnávací ořez",
    "min_remnant_mm": "Minimální využitelný zbytek",
    "time_limit_s": "Časový limit",
    "objective": "Cíl optimalizace",
}
FIELD_LABEL = {"name": "název", "length_mm": "délka", "quantity": "počet", "price": "cena"}


def build_changes(proposal: ChangeProposal, base: Project, diff: ProposalDiff) -> ChangesView:
    """Souhrn změn česky, odebrané řádky k vrácení."""
    names = {part.id: part.name for part in proposal.parts if part.name}
    lines: list[str] = []
    for part in proposal.parts:
        if part.id in diff.added_parts:
            lines.append(f"Nový díl: {_part(part.name, part.length_mm, part.quantity)}")
    for stock in proposal.stock:
        if stock.id in diff.added_stock:
            lines.append(f"Nová skladová délka: {_mm(stock.length_mm)}")
    lines += [_changed(change, proposal, names) for change in diff.changed]
    lines += [
        f"Odebraný díl: {_part(part.name, part.length_mm, part.quantity)}"
        for part in diff.removed_parts
    ]
    lines += [f"Odebraná skladová délka: {_mm(s.length_mm)}" for s in diff.removed_stock]
    return ChangesView(
        base_revision=base.revision,
        summary=tuple(lines),
        removed_parts=tuple(
            RemovedPartView(id=p.id, name=p.name, length_mm=p.length_mm, quantity=p.quantity)
            for p in diff.removed_parts
        ),
        removed_stock=tuple(
            RemovedStockView(id=s.id, length_mm=s.length_mm, price=s.price)
            for s in diff.removed_stock
        ),
    )


def previous_values(diff: ProposalDiff) -> dict[FieldPath, str]:
    """Původní hodnota změněných buněk, jak ji ukáže tabulka („původně 1 800“)."""
    return {change.path: format_value(change.path, change.before) for change in diff.changed}


def format_value(path: FieldPath, value: Value) -> str:
    field = str(path[-1])
    if value is None:
        return "prázdné"
    if isinstance(value, Objective):
        return OBJECTIVE_LABEL[value]
    if field == "price" and isinstance(value, Decimal):
        whole, fraction = f"{value:,.2f}".split(".")
        return f"{whole.replace(',', NBSP)},{fraction}{NBSP}Kč"
    if field.endswith("_mm") and isinstance(value, int | Decimal):
        return millimeters(value)
    if field == "quantity" and isinstance(value, int):
        return f"{number(value)}{NBSP}ks"
    if field == "time_limit_s" and isinstance(value, int):
        return f"{value}{NBSP}s"
    return str(value)


def _changed(change: FieldChange, proposal: ChangeProposal, names: dict[str, str]) -> str:
    path = change.path
    arrow = f"{format_value(path, change.before)} → {format_value(path, change.after)}"
    match path:
        case ("problem", "parts", int(index), str(field)):
            name = names.get(proposal.parts[index].id) or f"díl {index + 1}"
            return f"{name}: {FIELD_LABEL.get(field, field)} {arrow}"
        case ("problem", "stock", int(index), str(field)):
            length = proposal.stock[index].length_mm
            label = f"skladová délka {_mm(length)}" if length else f"skladová délka {index + 1}"
            return f"{label[:1].upper()}{label[1:]}: {FIELD_LABEL.get(field, field)} {arrow}"
        case ("parameters", str(field)):
            return f"{PARAMETER_LABEL.get(field, field)}: {arrow}"
        case ("problem", "material"):
            return f"Materiál: {arrow}"
        case _:
            return f"Název zakázky: {arrow}"


def _part(name: str | None, length: int | None, quantity: int | None) -> str:
    label = name or "bez názvu"
    size = _mm(length) if length is not None else "bez délky"
    count = f"{number(quantity)}{NBSP}ks" if quantity is not None else "bez počtu"
    return f"{label} {size} × {count}"


def _mm(value: int | None) -> str:
    return millimeters(value) if value is not None else "bez délky"
