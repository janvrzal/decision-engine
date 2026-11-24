"""Převod nedůvěryhodného vstupu na zakázku 1D a doménové kontroly (ADR-0001).

`parse_project` je jediná brána, kudy se vstup (import JSON, API, výstup modelu) stane
zakázkou. Výjimky Pydanticu nikdy neprojdou ven: vrací se `Err` se všemi chybami po polích.
"""

from collections import Counter
from collections.abc import Iterable, Sized

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from decision_engine.core.errors import FieldError
from decision_engine.core.model.cutting_1d import MAX_PIECES, Objective, Project
from decision_engine.core.result import Err, Ok, Result

type ProjectResult = Result[Project, tuple[FieldError, ...]]

NBSP = "\u00a0"


def parse_project(data: object) -> ProjectResult:
    """Ověří vstup a vrátí platnou zakázku, nebo všechny chyby po polích najednou."""
    try:
        project = Project.model_validate(data)
    except ValidationError as error:
        details = (detail for detail in error.errors() if not _is_spurious(detail))
        return Err(tuple(_field_error(detail) for detail in details))
    return validate_project(project)


def validate_project(project: Project) -> ProjectResult:
    """Doménové kontroly, které typy nevyjádří (identita, ořez, ceny pro zvolený cíl).

    Díl delší než všechny tyče chybou není: solver ho vede jako neumístěný kus (UC-01).
    """
    errors = (
        *_duplicate_ids("parts", (part.id for part in project.problem.parts), "jiný díl"),
        *_duplicate_ids(
            "stock", (stock.id for stock in project.problem.stock), "jiná skladová délka"
        ),
        *_trim_errors(project),
        *_missing_price_errors(project),
        *_too_many_pieces(project),
    )
    return Err(errors) if errors else Ok(project)


def _duplicate_ids(collection: str, ids: Iterable[str], owner: str) -> tuple[FieldError, ...]:
    """Chyba u každého dalšího výskytu stejného `id`; první výskyt zůstává platný."""
    ids = tuple(ids)
    duplicates = {item for item, count in Counter(ids).items() if count > 1}
    first_index = {item: ids.index(item) for item in duplicates}
    return tuple(
        FieldError(
            path=("problem", collection, index, "id"),
            code="duplicate_id",
            message=f"Tento identifikátor už má {owner}.",
        )
        for index, item in enumerate(ids)
        if item in duplicates and index != first_index[item]
    )


def _trim_errors(project: Project) -> tuple[FieldError, ...]:
    shortest = min(stock.length_mm for stock in project.problem.stock)
    if project.parameters.trim_mm < shortest:
        return ()
    return (
        FieldError(
            path=("parameters", "trim_mm"),
            code="trim_too_long",
            message=f"Ořez musí být kratší než nejkratší skladová délka ({_mm(shortest)}).",
        ),
    )


def _missing_price_errors(project: Project) -> tuple[FieldError, ...]:
    if project.parameters.objective is not Objective.CHEAPEST:
        return ()
    return tuple(
        FieldError(
            path=("problem", "stock", index, "price"),
            code="missing_price",
            message="Pro cíl „Nejnižší cena“ doplňte cenu, nebo zvolte jiný cíl.",
        )
        for index, stock in enumerate(project.problem.stock)
        if stock.price is None
    )


def _too_many_pieces(project: Project) -> tuple[FieldError, ...]:
    total = sum(part.quantity for part in project.problem.parts)
    if total <= MAX_PIECES:
        return ()
    return (
        FieldError(
            path=("problem", "parts"),
            code="too_many_pieces",
            message=(
                f"Zakázka má {_number(total)} kusů, aplikace spočítá nejvýš "
                f"{_number(MAX_PIECES)}. Zkontrolujte počty, nebo zakázku rozdělte."
            ),
        ),
    )


def _number(value: object) -> str:
    return f"{value:,}".replace(",", NBSP)


def _mm(value: int) -> str:
    return f"{value:,}".replace(",", NBSP) + f"{NBSP}mm"


# --- Převod chyb Pydanticu ---------------------------------------------------

_SIMPLE: dict[str, tuple[str, str]] = {
    "missing": ("required", "Chybí hodnota."),
    "string_too_short": ("required", "Chybí hodnota."),
    "too_short": ("empty", "Seznam nesmí být prázdný."),
    "decimal_max_places": ("too_precise", "Částka smí mít nejvýš 2 desetinná místa."),
    "decimal_parsing": ("not_number", "Zadejte číslo."),
    "decimal_type": ("not_number", "Zadejte číslo."),
    "enum": ("invalid_choice", "Neznámá volba."),
    "literal_error": ("invalid_choice", "Neznámá volba."),
    "extra_forbidden": ("unknown_field", "Neznámé pole."),
}

_NOT_INTEGER = frozenset({"int_parsing", "int_from_float", "int_type"})


def _is_spurious(detail: ErrorDetails) -> bool:
    """Pydantic hlásí „seznam je krátký“ i u neprázdného seznamu s neplatnou položkou.

    Taková chyba je zavádějící: skutečná chyba je u položky a ta se hlásí zvlášť.
    """
    value = detail["input"]
    return detail["type"] == "too_short" and isinstance(value, Sized) and len(value) > 0


def _field_error(detail: ErrorDetails) -> FieldError:
    path = tuple(detail["loc"])
    code, message = _code_and_message(detail, path)
    return FieldError(path=path, code=code, message=message)


def _code_and_message(detail: ErrorDetails, path: tuple[str | int, ...]) -> tuple[str, str]:
    kind = detail["type"]
    context = detail.get("ctx", {})
    in_mm = bool(path) and str(path[-1]).endswith("_mm")
    if kind == "decimal_max_places" and in_mm:
        return "too_precise", "Délka smí mít nejvýš 1 desetinné místo (mm)."
    if kind in _SIMPLE:
        return _SIMPLE[kind]
    if kind in _NOT_INTEGER:
        message = "Zadejte celé číslo v milimetrech." if in_mm else "Zadejte celé číslo."
        return "not_integer", message
    if kind == "greater_than":
        return "too_small", f"Hodnota musí být větší než {context.get('gt')}."
    if kind == "greater_than_equal":
        return "too_small", f"Hodnota musí být alespoň {context.get('ge')}."
    if kind in ("less_than_equal", "less_than"):
        limit = context.get("le", context.get("lt"))
        return "too_large", f"Hodnota smí být nejvýš {_number(limit)}."
    if kind == "string_too_long":
        return "too_long", f"Text smí mít nejvýš {context.get('max_length')} znaků."
    if kind == "too_long":
        return "too_long", f"Seznam smí mít nejvýš {_number(context.get('max_length'))} položek."
    return "invalid", "Neplatná hodnota."
