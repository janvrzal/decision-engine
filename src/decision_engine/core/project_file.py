"""Soubor zakázky v JSON: uložení a načtení (UC-06, spec kap. 7 Soubor zakázky).

Soubor je potvrzená zakázka (`Project`) bez dialogu, výsledku a klíčů. Načtený soubor
se nestane zakázkou hned: vznikne z něj návrh změny, který uživatel zkontroluje
a potvrdí (R1). Neplatný soubor (E1) vrátí srozumitelnou chybu, částečně neplatná data
(E2) projdou jako návrh a chyby ukáže kontrolní tabulka: hodnota nečekaného typu se
načte jako prázdná a označí (`file_errors`), takže ji uživatel doplní v tabulce.
"""

import json
from typing import Any, cast

from pydantic import BaseModel, TypeAdapter, ValidationError

from decision_engine.core.errors import FieldPath
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)
from decision_engine.core.result import Err, Ok, Result

FORMAT_VERSION = 1
NOT_A_PROJECT = "Soubor není zakázka DecisionEngine."
BROKEN_VALUES = "Některé hodnoty v souboru mají nečekaný tvar, soubor je nejspíš poškozený."


def write_project_file(project: Project) -> str:
    """Zakázka jako čitelný JSON (UTF-8, ceny jako text, aby se neztratila přesnost)."""
    return project.model_dump_json(indent=2) + "\n"


def read_project_file(content: str) -> Result[ChangeProposal, str]:
    """Návrh z obsahu souboru, nebo česká věta, proč soubor nejde načíst."""
    try:
        data: object = json.loads(content)
    except (ValueError, RecursionError):
        # Hluboce vnořený JSON vyčerpá zásobník parseru; i to je „není zakázka“.
        return Err(NOT_A_PROJECT)
    as_dict = _as_dict(data)
    return Err(NOT_A_PROJECT) if as_dict is None else _from_dict(as_dict)


def _as_dict(value: object) -> dict[str, Any] | None:
    """JSON objekt jako slovník s textovými klíči, jinak `None`."""
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in cast(dict[Any, Any], value).items()}


def _from_dict(data: dict[str, Any]) -> Result[ChangeProposal, str]:
    if "format_version" not in data or "task_type" not in data:
        return Err(NOT_A_PROJECT)
    version = data["format_version"]
    if version != FORMAT_VERSION:
        if isinstance(version, int) and not isinstance(version, bool) and version > 0:
            return Err(
                f"Soubor je z novější verze aplikace (formát {version}), tahle ho neumí načíst."
            )
        return Err(NOT_A_PROJECT)
    if data["task_type"] != "cutting_1d":
        return Err("Soubor obsahuje úlohu, kterou tahle verze aplikace neumí.")

    problem = _as_dict(data.get("problem"))
    if problem is None:
        return Err("V souboru chybí díly a skladové délky.")
    if not isinstance(problem.get("parts"), list):
        return Err("V souboru chybí díly.")
    if not isinstance(problem.get("stock"), list):
        return Err("V souboru chybí skladové délky.")
    parameters = _as_dict(data.get("parameters", {}))
    if parameters is None:
        return Err(BROKEN_VALUES)
    rows = _rows(cast(list[object], problem["parts"]), cast(list[object], problem["stock"]))
    if rows is None:
        return Err(BROKEN_VALUES)
    parts, stock, errors = rows
    clean_parameters, parameter_errors = _clean(ParametersDraft, parameters, ("parameters",))
    errors |= parameter_errors
    name = _text(data.get("name"), ("name",), errors)
    material = _text(problem.get("material"), ("problem", "material"), errors)

    try:
        proposal = ChangeProposal(
            base_revision=None,
            name=name,
            material=material,
            parts=tuple(PartDraft.model_validate(part) for part in parts),
            stock=tuple(StockLengthDraft.model_validate(item) for item in stock),
            parameters=ParametersDraft.model_validate(clean_parameters),
            origin="file",
            unconfirmed=frozenset(errors),
            file_errors=frozenset(errors),
        )
    except ValidationError:  # pragma: no cover - hodnoty už prošly kontrolou po polích
        return Err(BROKEN_VALUES)
    return Ok(proposal)


_Rows = tuple[list[dict[str, Any]], list[dict[str, Any]], set[FieldPath]]


def _rows(parts: list[object], stock: list[object]) -> _Rows | None:
    """Řádky dílů a skladových délek s platnými hodnotami; `None`, není-li řádek objekt."""
    errors: set[FieldPath] = set()
    clean_parts: list[dict[str, Any]] = []
    clean_stock: list[dict[str, Any]] = []
    for collection, items, model, target, prefix in (
        ("parts", parts, PartDraft, clean_parts, "p"),
        ("stock", stock, StockLengthDraft, clean_stock, "s"),
    ):
        used: set[str] = set()
        for index, item in enumerate(items):
            row = _as_dict(item)
            if row is None:
                return None
            clean, row_errors = _clean(model, row, ("problem", collection, index))
            errors |= row_errors
            clean["id"] = _row_id(clean.get("id"), prefix, index, used)
            target.append(clean)
    return clean_parts, clean_stock, errors


def _row_id(value: object, prefix: str, index: int, used: set[str]) -> str:
    """Id řádku ze souboru; chybí-li, vznikne nové. Duplicitu v souboru ukáže validace."""
    if isinstance(value, str) and value.strip():
        row_id = value
    else:
        row_id = f"{prefix}{index + 1}"
        while row_id in used:
            row_id = f"{row_id}x"
    used.add(row_id)
    return row_id


def _clean(
    model: type[BaseModel], values: dict[str, Any], path: FieldPath
) -> tuple[dict[str, Any], set[FieldPath]]:
    """Známá pole s hodnotou správného typu; neplatná hodnota se vynechá a označí."""
    clean: dict[str, Any] = {}
    errors: set[FieldPath] = set()
    for field, info in model.model_fields.items():
        value = values.get(field)
        if value is None or info.annotation is None:
            continue
        if field == "id":
            if isinstance(value, str):
                clean[field] = value
            continue
        try:
            if isinstance(value, bool):
                raise ValueError("pravdivostní hodnota není číslo ani text")
            clean[field] = TypeAdapter[object](info.annotation).validate_python(value)
        except (ValidationError, ValueError):
            errors.add((*path, field))
    return clean, errors


def _text(value: object, path: FieldPath, errors: set[FieldPath]) -> str | None:
    """Text ze souboru; jiný typ se načte jako prázdný a označí."""
    if value is None or isinstance(value, str):
        return value
    errors.add(path)
    return None
