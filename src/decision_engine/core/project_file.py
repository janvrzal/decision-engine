"""Soubor zakázky v JSON: uložení a načtení (UC-06, spec kap. 7 Soubor zakázky).

Soubor je potvrzená zakázka (`Project`) bez dialogu, výsledku a klíčů. Načtený soubor
se nestane zakázkou hned: vznikne z něj návrh změny, který uživatel zkontroluje
a potvrdí (R1). Neplatný soubor (E1) vrátí srozumitelnou chybu, částečně neplatná data
(E2) projdou jako návrh a chyby ukáže kontrolní tabulka.
"""

import json
from typing import Any, cast

from pydantic import ValidationError

from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.model.proposal import ChangeProposal
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
    except ValueError:
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
    parameters = data.get("parameters", {})
    if not isinstance(parameters, dict):
        return Err(BROKEN_VALUES)

    try:
        proposal = ChangeProposal.model_validate(
            {
                "base_revision": None,
                "name": data.get("name"),
                "material": problem.get("material"),
                "parts": problem["parts"],
                "stock": problem["stock"],
                "parameters": parameters,
                "origin": "file",
            }
        )
    except ValidationError:
        return Err(BROKEN_VALUES)
    return Ok(proposal)
