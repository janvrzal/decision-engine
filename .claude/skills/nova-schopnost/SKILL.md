---
name: nova-schopnost
description: Postup pro přidání nové schopnosti (např. cutting_2d, sklad) do registru schopností DecisionEngine. Použij, když se má implementovat nový typ úlohy, solver nebo modul nabízený routerem.
---

# Přidání nové schopnosti

Schopnost je záznam v registru (`src/decision_engine/capabilities/`), který spojuje: identifikátor, popis pro router, vstupní schéma, formulář, validaci, výpočet a prezentaci výsledku. Ostatní schopnosti se při přidání nesmí měnit.

## 1. Ověř rozsah

- Najdi schopnost ve `docs/specifikace.md` (kap. 3, příslušný UC, kap. 7, kap. 9).
- Pokud tam není nebo je popsaná vágně, **zastav se** a navrhni úpravu specifikace (skill `zmena-specifikace`). Neimplementuj podle vlastního výkladu.
- Sepiš kritéria přijetí z kap. 9 jako seznam testů, které musí na konci projít.

## 2. Navrhni a nech schválit

Před psaním kódu předlož uživateli krátký návrh:

- nové datové objekty v `core/` a jejich pole (jednotky podle ADR-0002),
- signaturu výpočtu: `solve(problem, parameters) -> Ok[CalculationResult] | Err[...]`,
- jak výsledek převede na `MaterialConsumption` pro kalkulaci,
- popis pro router (1–2 věty, česky, odlišitelné od ostatních schopností),
- zda je potřeba ADR (nový algoritmus, nová závislost → ano).

## 3. Implementuj zdola nahoru

1. `core/model/…` — neměnné Pydantic modely, `frozen=True`, `tuple`.
2. `core/validation/…` — validace s chybami po polích (`Err`), fyzická omezení (díl větší než deska, nulové počty…).
3. `core/solvers/<schopnost>/…` — solver; testy podle skillu `overeni-solveru`.
4. Převod výsledku na `MaterialConsumption`.
5. `capabilities/<schopnost>.py` — záznam v registru.
6. Vykreslení výsledku do SVG v `core/` (stejné SVG pro UI i PDF).
7. Události a větve reduceru, pokud schopnost přidává nové akce; testy v `tests/flow/`.
8. Extrakční schéma (Pydantic) a prompt v Langfuse + záložní kopie v `prompts/`; případy do `evals/extraction/dev/` a `evals/extraction/test/` (skill `ai-evaluace`).
9. View model v `api/`, `pnpm generate:api`, formulář a prezentace výsledku ve `frontend/` (skill `ui-frontend`).
10. Přidat identifikátor do množiny možností routeru **až ve chvíli, kdy je schopnost hotová** — router nesmí nabízet neimplementované.

## 4. Zkontroluj

- [ ] Ostatní schopnosti a jejich testy se nezměnily.
- [ ] Kalkulace funguje beze změny služby kalkulace.
- [ ] Router evaluace je přeměřena s novou možností (nová kategorie může zhoršit ostatní).
- [ ] Specifikace (kap. 3, 4, 9, 12) odpovídá stavu — rozšíření už není „podmíněné“, pokud je dokončené.
- [ ] Skill `priprava-pr`.
