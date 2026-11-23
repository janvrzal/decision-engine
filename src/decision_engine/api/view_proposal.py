"""View model návrhu změny (Krok Kontrola údajů): buňky, chyby, volby cíle."""

from collections.abc import Mapping
from decimal import Decimal

from decision_engine.api.view_model import (
    FieldErrorView,
    IntCell,
    MoneyCell,
    ObjectiveOption,
    ParametersView,
    PartRow,
    ProposalView,
    StockRow,
    TextCell,
)
from decision_engine.core.errors import FieldError, FieldPath
from decision_engine.core.model.cutting_1d import Objective
from decision_engine.core.model.proposal import ChangeProposal, confirm_proposal
from decision_engine.core.result import Err, Ok

OBJECTIVES: dict[Objective, tuple[str, str]] = {
    Objective.CHEAPEST: ("Nejnižší cena", "Co nejlevnější nákup tyčí podle jejich cen."),
    Objective.FEWEST_BARS: ("Nejméně tyčí", "Co nejméně tyčí k řezání a manipulaci."),
    Objective.LEAST_MATERIAL: ("Nejméně materiálu", "Co nejkratší součet délek tyčí."),
}
FIELD_LABELS = {
    "name": "název",
    "length_mm": "délka",
    "quantity": "počet",
    "price": "cena",
    "id": "označení",
    "kerf_mm": "Prořez",
    "trim_mm": "Zarovnávací ořez",
    "min_remnant_mm": "Minimální využitelný zbytek",
    "time_limit_s": "Časový limit",
    "objective": "Cíl optimalizace",
}
PARAMETER_FIELDS = ("kerf_mm", "trim_mm", "min_remnant_mm", "time_limit_s")


class _Cells:
    """Stav buněk návrhu: nepotvrzené hodnoty a chyby podle cesty pole."""

    def __init__(self, unconfirmed: frozenset[FieldPath], errors: Mapping[FieldPath, str]):
        self._unconfirmed = unconfirmed
        self._errors = errors

    def text(self, path: FieldPath, value: str | None) -> TextCell:
        return TextCell(
            value=value, unconfirmed=path in self._unconfirmed, error=self._errors.get(path)
        )

    def int(self, path: FieldPath, value: int | None) -> IntCell:
        return IntCell(
            value=value, unconfirmed=path in self._unconfirmed, error=self._errors.get(path)
        )

    def money(self, path: FieldPath, value: Decimal | None) -> MoneyCell:
        return MoneyCell(
            value=value, unconfirmed=path in self._unconfirmed, error=self._errors.get(path)
        )


def build_proposal(proposal: ChangeProposal, session_id: str) -> ProposalView:
    """Návrh s buňkami a živou validací (stejná pravidla jako při potvrzení)."""
    errors = _validate(proposal, session_id)
    cells = _Cells(proposal.unconfirmed, {error.path: error.message for error in errors})
    params = proposal.parameters
    all_priced = bool(proposal.stock) and all(s.price is not None for s in proposal.stock)
    return ProposalView(
        is_change=proposal.base_revision is not None,
        name=cells.text(("name",), proposal.name),
        material=cells.text(("problem", "material"), proposal.material),
        parts=tuple(
            PartRow(
                id=part.id,
                name=cells.text(("problem", "parts", i, "name"), part.name),
                length_mm=cells.int(("problem", "parts", i, "length_mm"), part.length_mm),
                quantity=cells.int(("problem", "parts", i, "quantity"), part.quantity),
            )
            for i, part in enumerate(proposal.parts)
        ),
        stock=tuple(
            StockRow(
                id=stock.id,
                length_mm=cells.int(("problem", "stock", i, "length_mm"), stock.length_mm),
                price=cells.money(("problem", "stock", i, "price"), stock.price),
            )
            for i, stock in enumerate(proposal.stock)
        ),
        parameters=ParametersView(
            kerf_mm=cells.int(("parameters", "kerf_mm"), params.kerf_mm),
            trim_mm=cells.int(("parameters", "trim_mm"), params.trim_mm),
            min_remnant_mm=cells.int(("parameters", "min_remnant_mm"), params.min_remnant_mm),
            time_limit_s=cells.int(("parameters", "time_limit_s"), params.time_limit_s),
        ),
        objective=params.objective,
        objective_unconfirmed=("parameters", "objective") in proposal.unconfirmed,
        objective_options=tuple(
            ObjectiveOption(
                value=objective,
                label=label,
                hint=hint,
                disabled_reason=(
                    "Chybí ceny skladových délek."
                    if objective is Objective.CHEAPEST and not all_priced
                    else None
                ),
            )
            for objective, (label, hint) in OBJECTIVES.items()
        ),
        errors=tuple(FieldErrorView(field=field_label(e.path), message=e.message) for e in errors),
        can_confirm=not errors,
        confirm_disabled_reason=confirm_disabled_reason(len(errors)),
    )


def _validate(proposal: ChangeProposal, session_id: str) -> tuple[FieldError, ...]:
    """Chyby, které by vrátilo potvrzení (revize na výsledek chyb nemá vliv)."""
    match confirm_proposal(proposal, session_id, revision=0):
        case Ok():
            return ()
        case Err(errors):
            return errors


def field_label(path: FieldPath) -> str:
    """Čitelné umístění chyby: „Díl 2, délka“, „Skladová délka 1, cena“, „Prořez“."""
    match path:
        case ("problem", "parts", int(index), str(field)):
            return f"Díl {index + 1}, {FIELD_LABELS.get(field, field)}"
        case ("problem", "stock", int(index), str(field)):
            return f"Skladová délka {index + 1}, {FIELD_LABELS.get(field, field)}"
        case ("problem", "parts" | "stock" as collection):
            return "Díly" if collection == "parts" else "Skladové délky"
        case ("parameters", str(field)) | (str(field),):
            label = FIELD_LABELS.get(field, field)
            return label[:1].upper() + label[1:]
        case _:
            return "Zakázka"


def confirm_disabled_reason(error_count: int) -> str | None:
    if error_count == 0:
        return None
    if error_count == 1:
        return "Opravte 1 pole, než spustíte výpočet."
    if error_count <= 4:
        return f"Opravte {error_count} pole, než spustíte výpočet."
    return f"Opravte {error_count} polí, než spustíte výpočet."
