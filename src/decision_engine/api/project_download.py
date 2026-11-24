"""Stažení souboru zakázky (UC-06): obsah skládá jádro, tady jen název a hlavičky."""

import re
import unicodedata
from urllib.parse import quote

from fastapi import Response

from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.project_file import write_project_file

SUFFIX = ".decision.json"
REVISION_HEADER = "X-Project-Revision"
"""Revize ve staženém souboru; frontend ji pošle zpět v `ProjectSaved`."""


def file_name(project_name: str) -> str:
    """Název souboru z názvu zakázky bez diakritiky: „Regál do dílny“ → regal-do-dilny."""
    ascii_name = (
        unicodedata.normalize("NFKD", project_name).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return f"{slug or 'zakazka'}{SUFFIX}"


def project_file_response(project: Project) -> Response:
    name = file_name(project.name)
    return Response(
        content=write_project_file(project),
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}",
            REVISION_HEADER: str(project.revision),
        },
    )
