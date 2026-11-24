"""Rozhodnutí routeru a odpovědi aplikace na ně (spec kap. 6 Router, UC-05, ADR-0012).

Router jen rozpozná, o jakou úlohu jde; co se pak stane, rozhoduje reducer podle
`RoutingDecision`. Texty odpovědí na nejasné a nepodporované zadání jsou tady, ne
v promptu: aplikace nevymýšlí čísla a doptání je vždy konkrétní.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.calculation import CalculationResult
from decision_engine.core.model.cutting_1d import Project
from decision_engine.core.render.format import money

type Intent = Literal["new_order", "change_order", "result_question"]
type Capability = Literal["cutting_1d", "cost_estimate"]


class RouteOutcome(StrEnum):
    SUPPORTED = "supported"
    UNCLEAR = "unclear"
    UNSUPPORTED = "unsupported"


class RoutingDecision(BaseModel):
    """Co router rozpoznal (spec kap. 7 `RoutingDecision`)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    outcome: RouteOutcome
    capability: Capability | None = None
    intent: Intent | None = None
    question: str | None = None
    """Konkrétní doptávací otázka (jen LLM router); jinak použije aplikace výchozí."""
    router: str
    """Implementace, která rozhodla (`jev`, `llm`, `manual`)."""
    fallback_reason: str | None = None
    """Proč rozhodla záložní implementace (výpadek nebo chybějící klíč předchozí)."""


NO_ORDER = "žádná – uživatel zatím nic nezadal"

UNCLEAR_TEXT = (
    "Co přesně potřebujete nařezat? Napište díly s délkou a počtem kusů "
    "(např. „4 nohy po 1 800 mm“) a délku tyčí, ze kterých řežete."
)
UNSUPPORTED_TEXT = (
    "Tohle zatím neumím. Umím spočítat nářezový plán tyčí, profilů a trubek a cenu "
    "materiálu. Díly můžete zadat i ručně tlačítkem „Zadat ručně“."
)
RESULT_QUESTION_TEXT = (
    "Na otázky k hotovému plánu zatím neodpovídám. Polohy řezů najdete v rozpisu po tyčích, "
    "spotřebu, zbytky a odpad v metrikách výsledku."
)
NO_PLAN_COST_TEXT = (
    "Cenu materiálu spočítám z plánu. Nejdřív zadejte díly a skladové délky s cenou "
    "a spusťte výpočet; cena se ukáže u výsledku."
)


def order_summary(project: Project | None, result: CalculationResult | None) -> dict[str, object]:
    """Rozpracovaná zakázka pro router: jen to, co člověk potřebuje k posouzení zprávy."""
    if project is None:
        return {"rozpracovana_zakazka": NO_ORDER}
    problem = project.problem
    plan = "zatím nespočítaný"
    if result is not None and result.source.revision == project.revision:
        plan = f"spočítaný: {len(result.bars)} tyčí"
    return {
        "rozpracovana_zakazka": {
            "ulohy": "řezání tyčí (1D)",
            "dily": [
                {"nazev": part.name, "delka_mm": part.length_mm, "pocet": part.quantity}
                for part in problem.parts
            ],
            "skladove_delky_mm": [stock.length_mm for stock in problem.stock],
            "prorez_mm": str(project.parameters.kerf_mm),
            "plan": plan,
        }
    }


def cost_text(total: Decimal | None) -> str:
    """Odpověď na dotaz na cenu: jen spočítaná cena materiálu, nic odhadnutého."""
    if total is None:
        return (
            "Cenu materiálu nejde sečíst: u některé spotřebované skladové délky chybí cena. "
            "Doplňte ji v kroku Kontrola údajů. Práci, přirážku a DPH kalkulace zatím neumí."
        )
    amount = money(total)
    return (
        f"Orientační cena materiálu podle plánu je {amount} (spotřebované tyče × cena za kus). "
        "Práci, přirážku a DPH kalkulace zatím neumí."
    )
