---
name: overeni-solveru
description: Jak testovat a ověřovat solvery DecisionEngine (1D řezání tyčí, 2D řezání desek, sklad) — invarianty, property-based testy, porovnání s úplným prohledáním a pravidla pro štítek „optimální“. Použij při psaní nebo změně solveru či jeho testů.
---

# Ověření solveru

Solver je správný, když každý výstup splňuje invarianty a štítek odpovídá tomu, co je skutečně prokázané. Rychlost je až druhá.

## 1. Nezávislý validátor

Pro každý typ výsledku existuje v `core/` funkce `check_<schopnost>(problem, parameters, result) -> tuple[Violation, ...]`, která **nepoužívá kód solveru**. Kontroluje:

**1D**
- každý požadovaný kus (podle identity, ne jen rozměru) je umístěn právě jednou, nebo je v seznamu neumístěných,
- kapacita každé tyče: Σ lᵢ + n·k ≤ L + k − zarovnávací ořez (UC-01),
- zbytek ≥ minimální délka → využitelný zbytek, jinak odpad,
- metriky (spotřeba, výtěžnost, odpad) přepočítané nezávisle souhlasí,
- se skladem: počet použitých kusů dané položky ≤ počet na skladě.

**2D**
- díly uvnitř použitelné oblasti (po okrajovém ořezu), bez překryvu, mezery ≥ prořez,
- rotace jen o 90° a jen u povolených dílů,
- posloupnost řezů je gilotinová a skutečně vede k uvedeným dílům.

Validátor se volá v každém testu solveru a v debug režimu i za běhu.

## 2. Typy testů

| Typ | Kde | Co |
|---|---|---|
| Příklady | `tests/unit/` | Ručně spočítané malé případy, hraniční hodnoty (kus = délka tyče, nulový prořez, kus delší než všechny tyče) |
| Property-based | `tests/property/` | `hypothesis` generuje náhodné instance; validátor nesmí najít porušení; heuristika ≥ dolní mez |
| Porovnání s optimem | `tests/property/` | Malé instance (≤ ~10 kusů) se řeší úplným prohledáním; hodnota solveru = optimum, a pokud solver tvrdí „optimální“, musí se rovnat |
| Regrese | `tests/unit/` | Každá nalezená chyba dostane vlastní test s instancí, která ji odhalila |
| Výkon | `tests/perf/` (marker `slow`) | Demo sady (~100 kusů 1D, ~30 kusů 2D) do 10 s; čas se zapíše, ne jen ověří |

Úplné prohledání (brute force) je samostatná, co nejjednodušší implementace v testech — nesdílí kód se solverem.

## 3. Pravidla pro štítek

- `optimal` jen pokud hodnota cíle = ⌈dolní mez⌉ (1D z LP relaxace), nebo CP-SAT vrátil `OPTIMAL` nad modelem, který je dokázaně ekvivalentní úloze.
- Jinak `best_found` a výsledek nese dolní mez, aby UI mohlo ukázat rozdíl.
- Test: pro každou instanci, kde solver vrátí `optimal`, brute force nesmí najít lepší řešení.
- Test: časový limit 0/velmi krátký vrátí platné řešení z heuristiky se štítkem `best_found`, ne chybu.

## 4. Determinismus

Solver je čistá funkce. Pokud používá náhodu (např. pořadí v heuristice), dostává `seed` v `Parameters`. CP-SAT běží s pevným počtem workerů nebo se test nespoléhá na konkrétní rozmístění, jen na hodnotu cíle a invarianty.

## 5. Před dokončením

- [ ] Validátor pokrývá všechny podmínky z kap. 9 specifikace pro danou schopnost.
- [ ] Property testy běží s alespoň 200 příklady (`@settings(max_examples=200)`) a v CI projdou do rozumného času.
- [ ] Brute force porovnání pokrývá každý cíl optimalizace.
