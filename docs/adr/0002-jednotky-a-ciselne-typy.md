# ADR-0002: Délky v celých milimetrech, peníze v Decimal

**Stav:** přijato; bod o desetinách milimetru nahrazen ADR-0011 (prořez a ořez)  
**Datum:** 2026-11-23  
**Souvisí se:** specifikace UC-01, UC-04

## Kontext

Plovoucí čárka způsobuje chyby v kapacitních podmínkách (součet délek + prořez ≤ délka tyče) i v penězích. Solvery OR-Tools (CP-SAT) navíc pracují s celými čísly.

## Rozhodnutí

- Všechny délky a rozměry v jádře jsou `int` v milimetrech. Převod jednotek ze zadání („2 m“, „150 cm“) proběhne jen ve validaci vstupu.
- Peněžní částky jsou `decimal.Decimal`; zaokrouhlení jednotně `ROUND_HALF_UP` na 2 desetinná místa až v definovaných bodech kalkulace.
- `float` se v jádře pro délky ani peníze nepoužívá; výjimkou jsou poměry (výtěžnost) a hodnoty LP relaxace.

## Zvažované varianty

- **Desetiny milimetru** — zbytečná přesnost pro dílenské řezání; prořez se zadává v celých mm.
- **`float` s tolerancí** — křehké a těžko testovatelné.

## Důsledky

- Zadání s přesností pod 1 mm se zaokrouhlí a uživatel to uvidí v kontrolní tabulce.
- Přechod na jemnější jednotku by znamenal změnu formátu zakázky (nová verze formátu).
