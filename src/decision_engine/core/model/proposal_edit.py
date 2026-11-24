"""Úprava návrhu změny v kontrolní tabulce (R1, R6).

Uživatel pošle celý nový obsah návrhu. Hodnota, kterou změnil, je jeho vlastní, a proto
přestane být nepotvrzená. Nezměněné nepotvrzené hodnoty zůstanou označené; řádky se
sledují podle `id`, takže smazání nebo přesun řádku označení nepomíchá. Neplatná hodnota
ze souboru zůstane označená, dokud ji uživatel nevyplní.
"""

from decision_engine.core.errors import FieldPath
from decision_engine.core.model.proposal import (
    ChangeProposal,
    ParametersDraft,
    PartDraft,
    StockLengthDraft,
)


def edit_proposal(
    proposal: ChangeProposal,
    *,
    name: str | None,
    material: str | None,
    parts: tuple[PartDraft, ...],
    stock: tuple[StockLengthDraft, ...],
    parameters: ParametersDraft,
) -> ChangeProposal:
    """Nový návrh s upraveným obsahem a přepočteným označením nepotvrzených hodnot."""
    edited = proposal.model_copy(
        update={
            "name": name,
            "material": material,
            "parts": parts,
            "stock": stock,
            "parameters": parameters,
        }
    )
    still = {
        moved
        for path in proposal.unconfirmed
        if (moved := _follow(path, proposal, edited)) is not None
        and _value(proposal, path) == _value(edited, moved)
    }
    still_broken = {
        moved
        for path in proposal.file_errors
        if (moved := _follow(path, proposal, edited)) is not None and _value(edited, moved) is None
    }
    return edited.model_copy(
        update={"unconfirmed": frozenset(still), "file_errors": frozenset(still_broken)}
    )


def _follow(path: FieldPath, old: ChangeProposal, new: ChangeProposal) -> FieldPath | None:
    """Cesta ke stejnému poli v novém návrhu (řádky podle `id`), nebo `None`."""
    match path:
        case ("problem", "parts" | "stock" as collection, int(index), str(field)):
            old_rows = old.parts if collection == "parts" else old.stock
            new_rows = new.parts if collection == "parts" else new.stock
            if index >= len(old_rows):
                return None
            row_id = old_rows[index].id
            new_index = next((i for i, row in enumerate(new_rows) if row.id == row_id), None)
            return None if new_index is None else ("problem", collection, new_index, field)
        case _:
            return path


def _value(proposal: ChangeProposal, path: FieldPath) -> object:
    match path:
        case ("problem", "parts", int(index), str(field)):
            return getattr(proposal.parts[index], field, None)
        case ("problem", "stock", int(index), str(field)):
            return getattr(proposal.stock[index], field, None)
        case ("parameters", str(field)):
            return getattr(proposal.parameters, field, None)
        case ("problem", "material"):
            return proposal.material
        case (str(field),):
            return getattr(proposal, field, None)
        case _:
            return None
