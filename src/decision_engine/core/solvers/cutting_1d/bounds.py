"""Dolní mez hodnoty cíle a hodnota cíle plánu 1D (spec kap. 8, skill `overeni-solveru`).

Kapacitní podmínka tyče délky L: Σ(lᵢ + k) ≤ L - ořez + k (k = prořez). Každý kus tedy
spotřebuje „místo“ lᵢ + k a tyč ho nabízí L - ořez + k. Spojitá relaxace: celé potřebné
místo pokryjeme skladovou délkou s nejlepším poměrem ceny cíle na nabízené místo. To je
platná dolní mez pro každý cíl; dosáhne-li jí plán (po zaokrouhlení na jednotku cíle),
je prokazatelně optimální.
"""

import math
from decimal import ROUND_CEILING, Decimal

from decision_engine.core.model.calculation import Bar
from decision_engine.core.model.cutting_1d import Objective, Project, StockLength

CENT = Decimal("0.01")


def lower_bound(project: Project, pieces: list[int]) -> Decimal | None:
    """Dolní mez cíle pro umístění kusů dané délky; `None`, když ji nejde spočítat.

    Mez je zaokrouhlená nahoru na jednotku cíle (tyč, mm, haléř), protože hodnota cíle
    je vždy celý násobek té jednotky.
    """
    params = project.parameters
    space = sum((Decimal(length) + params.kerf_mm for length in pieces), Decimal(0))
    if space == 0:
        return Decimal(0)
    ratios = [
        _cost(stock, params.objective) / capacity
        for stock in project.problem.stock
        if (capacity := Decimal(stock.length_mm) - params.trim_mm + params.kerf_mm) > 0
        and (params.objective is not Objective.CHEAPEST or stock.price is not None)
        and any(Decimal(length) <= capacity - params.kerf_mm for length in pieces)
    ]
    if not ratios:
        return None
    bound = space * min(ratios)
    if params.objective is Objective.CHEAPEST:
        return bound.quantize(CENT, rounding=ROUND_CEILING)
    return Decimal(math.ceil(bound))


def objective_value(project: Project, bars: tuple[Bar, ...]) -> Decimal | None:
    """Hodnota cíle plánu: počet tyčí, součet jejich délek, nebo cena; `None` bez ceny."""
    match project.parameters.objective:
        case Objective.FEWEST_BARS:
            return Decimal(len(bars))
        case Objective.LEAST_MATERIAL:
            return Decimal(sum(bar.length_mm for bar in bars))
        case Objective.CHEAPEST:
            prices = {stock.id: stock.price for stock in project.problem.stock}
            total = Decimal(0)
            for bar in bars:
                price = prices.get(bar.stock_id)
                if price is None:
                    return None
                total += price
            return total


def _cost(stock: StockLength, objective: Objective) -> Decimal:
    match objective:
        case Objective.FEWEST_BARS:
            return Decimal(1)
        case Objective.LEAST_MATERIAL:
            return Decimal(stock.length_mm)
        case Objective.CHEAPEST:
            return stock.price if stock.price is not None else Decimal(0)
