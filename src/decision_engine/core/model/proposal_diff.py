"""Změny návrhu oproti potvrzené revizi (spec kap. 4: souhrn změn při navazující úpravě).

Řádky se párují podle `id`, takže přesun řádku není změna. Výsledek říká, co přibylo,
co se změnilo (s původní hodnotou) a co návrh odebral; UI z toho ukáže souhrn
a zvýraznění a odebraný řádek umí vrátit.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.errors import FieldPath
from decision_engine.core.model.cutting_1d import Objective, Project
from decision_engine.core.model.proposal import ChangeProposal

type Value = str | int | Decimal | Objective | None


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class FieldChange(_Frozen):
    """Pole návrhu s jinou hodnotou než v potvrzené revizi; cesta je v souřadnicích návrhu."""

    path: FieldPath
    before: Value
    after: Value


class RemovedPart(_Frozen):
    id: str
    name: str
    length_mm: int
    quantity: int


class RemovedStock(_Frozen):
    id: str
    length_mm: int
    price: Decimal | None


class ProposalDiff(_Frozen):
    added_parts: tuple[str, ...]
    """`id` dílů, které v revizi nebyly."""
    added_stock: tuple[str, ...]
    changed: tuple[FieldChange, ...]
    removed_parts: tuple[RemovedPart, ...]
    removed_stock: tuple[RemovedStock, ...]

    @property
    def empty(self) -> bool:
        return not (
            self.added_parts
            or self.added_stock
            or self.changed
            or self.removed_parts
            or self.removed_stock
        )


_PARAMETERS = ("kerf_mm", "trim_mm", "min_remnant_mm", "time_limit_s", "objective")


def diff_proposal(proposal: ChangeProposal, base: Project) -> ProposalDiff:
    """Co se v návrhu liší od potvrzené revize `base`."""
    problem = base.problem
    old_parts = {part.id: part for part in problem.parts}
    old_stock = {stock.id: stock for stock in problem.stock}
    changed: list[FieldChange] = []

    for index, part in enumerate(proposal.parts):
        old = old_parts.get(part.id)
        if old is None:
            continue
        for field, before, after in (
            ("name", old.name, part.name),
            ("length_mm", old.length_mm, part.length_mm),
            ("quantity", old.quantity, part.quantity),
        ):
            if before != after:
                changed.append(
                    FieldChange(path=("problem", "parts", index, field), before=before, after=after)
                )
    for index, stock in enumerate(proposal.stock):
        old = old_stock.get(stock.id)
        if old is None:
            continue
        for field, before, after in (
            ("length_mm", old.length_mm, stock.length_mm),
            ("price", old.price, stock.price),
        ):
            if before != after:
                changed.append(
                    FieldChange(path=("problem", "stock", index, field), before=before, after=after)
                )
    for field in _PARAMETERS:
        before = getattr(base.parameters, field)
        after = getattr(proposal.parameters, field)
        if before != after:
            changed.append(FieldChange(path=("parameters", field), before=before, after=after))
    if (proposal.material or None) != problem.material:
        changed.append(
            FieldChange(
                path=("problem", "material"), before=problem.material, after=proposal.material
            )
        )
    if proposal.name is not None and proposal.name != base.name:
        changed.append(FieldChange(path=("name",), before=base.name, after=proposal.name))

    new_part_ids = {part.id for part in proposal.parts}
    new_stock_ids = {stock.id for stock in proposal.stock}
    return ProposalDiff(
        added_parts=tuple(p.id for p in proposal.parts if p.id not in old_parts),
        added_stock=tuple(s.id for s in proposal.stock if s.id not in old_stock),
        changed=tuple(changed),
        removed_parts=tuple(
            RemovedPart(id=p.id, name=p.name, length_mm=p.length_mm, quantity=p.quantity)
            for p in problem.parts
            if p.id not in new_part_ids
        ),
        removed_stock=tuple(
            RemovedStock(id=s.id, length_mm=s.length_mm, price=s.price)
            for s in problem.stock
            if s.id not in new_stock_ids
        ),
    )
