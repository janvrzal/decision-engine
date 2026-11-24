# ADR-0011: Prořez a zarovnávací ořez v desetinách milimetru

**Stav:** přijato  
**Datum:** 2026-11-24  
**Souvisí se:** specifikace UC-01, kap. 7 `Parameters` a Soubor zakázky; částečně nahrazuje ADR-0002 (bod „Desetiny milimetru“); Issue #49

## Kontext

ADR-0002 drží všechny délky jako `int` v milimetrech a desetiny milimetru odmítl jako zbytečnou přesnost. Recenze z pohledu dílny ukázala opak u prořezu: pásová pila má prořez 1,5–2 mm, kotoučová na kov 2,2–2,5 mm. Zaokrouhlení na celé mm u desítek řezů posune polohy řezů o centimetry a uživatel „2,5“ dnes nemůže zadat vůbec. Autor rozhodl, že prořez a ořez budou v desetinách milimetru.

## Rozhodnutí

- Prořez (`kerf_mm`) a zarovnávací ořez (`trim_mm`) jsou `Decimal` s nejvýš **jedním** desetinným místem, nezáporné, nejvýš 100 000 mm.
- Délky dílů, skladových délek a minimální využitelný zbytek zůstávají `int` v mm (ADR-0002 pro ně platí dál).
- Hodnoty odvozené od prořezu a ořezu — poloha začátku kusu (`PlacedPiece.start_mm`), polohy řezů, délka zbytku a odpadu — jsou `Decimal`. Geometrie, solver, metriky i nezávislý validátor počítají v `Decimal` přesně; `float` se pro délky nepoužívá (jen pro souřadnice při vykreslení SVG).
- API posílá tyto hodnoty jako řetězec `Decimal` (stejně jako ceny); frontend je jen formátuje v `cs-CZ` („2 005,5 mm“).
- Soubor zakázky zůstává ve formátu 1: celé číslo v `kerf_mm` je dál platné, nový soubor zapisuje `Decimal` jako text („2.5“).

## Zvažované varianty

- **Interně celé desetiny milimetru (`int`)** — rychlé, ale jednotka by prosakovala do modelu výsledku i API, nebo by bylo potřeba převádět na každé hranici; víc míst pro chybu.
- **Zaokrouhlit nahoru na celé mm s poznámkou** — beze změny modelu, ale plán by u desítek řezů neodpovídal pile; zamítnuto autorem.
- **`float`** — porušuje ADR-0002 a kapacitní podmínky by potřebovaly toleranci.

## Důsledky

- Polohy řezů odpovídají skutečné pile i pro prořez 1,6 nebo 2,5 mm.
- `Decimal` aritmetika je pomalejší; výkonový test (100 kusů, 5 000 kusů) zůstává hluboko pod limitem 10 s.
- Hlídá to: typy Pydanticu (`decimal_places=1`) s českou hláškou, property testy solveru s desetinným prořezem, validátor plánu a pyright (literály se musí předat jako `Decimal`).
- Přehodnotit, kdyby se objevil požadavek na desetiny u délek dílů (pak spíš jednotka 0,1 mm pro všechny délky).
