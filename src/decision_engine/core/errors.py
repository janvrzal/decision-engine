"""Chyby vstupních dat vázané na konkrétní pole, aby je UI mohlo ukázat u buňky."""

from pydantic import BaseModel, ConfigDict

type FieldPath = tuple[str | int, ...]
"""Cesta k poli od kořene zakázky, např. `("problem", "parts", 2, "length_mm")`."""


class FieldError(BaseModel):
    """Chyba jednoho pole: cesta k poli, strojový kód a česká hláška pro uživatele."""

    model_config = ConfigDict(frozen=True)

    path: FieldPath
    """Cesta od kořene vstupu, např. `("problem", "parts", 2, "length_mm")`; `()` = celý vstup."""
    code: str
    """Anglický identifikátor druhu chyby (`required`, `too_small`, `duplicate_id` …)."""
    message: str
    """Krátká česká hláška pro uživatele."""
