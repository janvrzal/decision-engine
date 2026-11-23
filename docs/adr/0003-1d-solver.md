# ADR-0003: 1D solver — heuristika, generování vzorů a CP-SAT

**Stav:** přijato  
**Datum:** 2026-11-23  
**Souvisí se:** specifikace UC-01, kap. 7 „1D solver“, kap. 8

## Kontext

Řezání tyčí s více skladovými délkami, prořezem, třemi cíli optimalizace a (v rozšíření) omezeným skladem. Štítek „optimální“ smí být jen při prokázaném optimu.

## Rozhodnutí

1. First Fit Decreasing rozšířený o výběr skladové délky podle cíle — okamžité platné řešení a horní mez.
2. Gilmore–Gomory column generation: LP relaxace nad vzory řezání, pomocná úloha batohu pro každou skladovou délku; LP hodnota je dolní mez.
3. Celočíselný výběr ze vzorů v CP-SAT s časovým limitem a startem z heuristiky.
4. „Optimální“ právě tehdy, když hodnota řešení = zaokrouhlená dolní mez; jinak „nejlepší nalezené“ s uvedením rozdílu.

## Zvažované varianty

- **Přímý model kus × tyč v CP-SAT** — jednoduchý, ale symetrie brání prokázání optima už u desítek kusů.
- **Pouze heuristika** — rychlé, ale nikdy nedokáže optimum; slabší výsledek pro práci.
- **MIP solver (např. HiGHS) pro celočíselnou část** — možné; CP-SAT je v OR-Tools k dispozici bez další závislosti.

## Důsledky

- Závislost na OR-Tools (LP solver GLOP a CP-SAT).
- Omezený sklad = horní meze na použití vzorů dané skladové položky; struktura se nemění.
- Testy porovnávají malé instance s úplným prohledáním (skill `overeni-solveru`).
