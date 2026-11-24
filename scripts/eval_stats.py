"""Statistika pro reporty evaluací (skill `ai-evaluace`): intervaly a párové srovnání.

Sady mají desítky případů, takže samotné procento nestačí: report uvádí 95% Wilsonův
interval a dva modely na stejných případech porovnává párově (přesný McNemarův test).
"""

import math


def wilson(correct: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilsonův interval pro podíl správných odpovědí."""
    if total == 0:
        return 0.0, 0.0
    p = correct / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def interval(correct: int, total: int) -> str:
    low, high = wilson(correct, total)
    return f"{correct}/{total} ({correct / max(total, 1):.0%}, 95% interval {low:.0%}–{high:.0%})"


def mcnemar(only_a: int, only_b: int) -> float:
    """Přesný oboustranný McNemarův test: p-hodnota pro případy, kde se modely liší."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)
