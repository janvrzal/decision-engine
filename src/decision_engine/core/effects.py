"""Efekty: popisy vedlejších účinků, které vykoná aplikační vrstva (ADR-0006).

Reducer efekty jen vrací. `app/` je vykoná přes porty a výsledek pošle zpět jako událost.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.cutting_1d import Project


class _Effect(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CallExtractor(_Effect):
    """Převeď zprávu na návrh změny. Výsledek: `ProposalReceived` nebo `AiFailed`."""

    type: Literal["CallExtractor"] = "CallExtractor"
    text: str
    base: Project | None
    """Potvrzená zakázka, vůči které je zpráva úpravou; `None` u nové zakázky."""


class RunSolver(_Effect):
    """Spočítej plán pro potvrzenou revizi. Výsledek: `SolveFinished`."""

    type: Literal["RunSolver"] = "RunSolver"
    project: Project


type Effect = CallExtractor | RunSolver
