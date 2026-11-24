# DecisionEngine

**Ze zadání k nářezovému plánu a ceně zakázky.** Webová aplikace pro malé dílny: zámečník nebo truhlář napíše zakázku česky tak, jak by ji řekl kolegovi, zkontroluje údaje v tabulce a dostane ověřený nářezový plán tyčí s polohami řezů a orientační cenou materiálu.

Semestrální práce z předmětu Generativní AI (téma 2, [zadání](docs/zadani.md)).

## Problém a řešení

Míry se v dílně píšou na papír a tyče se rozkládají odhadem: buď se jede do skladu podruhé, nebo zbude tyč navíc. Excel je na jednu zakázku moc práce a hotové optimalizátory chtějí vyplnit formulář.

DecisionEngine převede volné zadání na tabulku dílů ke kontrole, spočítá plán řezání a ukáže, kolik tyčí koupit a za kolik. Navazující změnu („přidej 4 příčky po 850 mm“) stačí napsat; aplikace ukáže, co se změnilo, a plán přepočítá až po potvrzení.

## Co dělá AI a co výpočet

| AI (Groq, TypeSafe Jev) | Program (ověřitelný výpočet) |
|---|---|
| Rozpozná, o jakou úlohu jde, a u nejasného zadání se doptá (router Jev / LLM / ruční) | Nářezový plán (FFD s časovým limitem), dolní mez a štítek „Optimální“ jen při jejím dosažení |
| Převede text na návrh zakázky ve validovaném schématu | Validace údajů, nezávislý validátor každého plánu |
| Napíše krátkou odpověď v dialogu | Cena materiálu, metriky, polohy řezů, souhrn změn |

AI nevymýšlí čísla: každé číslo od modelu musí mít oporu v zadání nebo v potvrzené zakázce, jinak je v tabulce označené jako „Odhad AI, ověřte.“ Zakázka se mění jen potvrzením uživatele.

## Stav

| Use case | Stav |
|---|---|
| UC-01 Nářezový plán tyčí | hotovo (FFD, dolní mez, štítky, prořez v desetinách mm) |
| UC-03 Navazující změna zakázky | hotovo (souhrn změn, zachování údajů) |
| UC-04 Orientační kalkulace | první etapa: cena materiálu; práce, přirážka, DPH a PDF v M5 |
| UC-05 Nejasné nebo nepodporované zadání | hotovo (router Jev / LLM / ruční, doptání) |
| UC-06 Uložení a načtení zakázky | hotovo (JSON, tisk plánu k pile) |
| UC-07 Výpadek AI | hotovo (ruční zadání, opakování zprávy) |
| UC-13 Ruční zadání | hotovo |
| UC-15 Nová zakázka | hotovo (ochrana neuložené práce) |
| UC-02 2D desky, UC-08 sklad | rozšíření, mimo semestrální rozsah |

Milníky M0–M3 a část M4–M6 jsou hotové; měření na testovacích sadách (M8) spouští autor ([evals/README.md](evals/README.md)).

## Spuštění

Potřebujete `uv`, `pnpm` a Node.js 22+ (`brew install uv pnpm node`).

```bash
uv sync
pnpm -C frontend install
pnpm -C frontend build
uv run decision-engine
```

Aplikace běží na <http://127.0.0.1:8000>. Bez klíčů AI funguje ruční zadání; klíče patří do `.env` (vzor v `.env.example`). Bez sítě lze projít hlavní tok nad připravenými odpověďmi:

```bash
LLM_REPLAY_FILE=frontend/e2e/fixtures/uc01.json uv run decision-engine
```

## Vývoj

```bash
uv run pre-commit install
uv run decision-engine          # backend na :8000
pnpm -C frontend dev            # frontend s hot reloadem, /api přes proxy na :8000
```

- Specifikace: [docs/specifikace.md](docs/specifikace.md)
- Rozhodnutí: [docs/adr/](docs/adr/)
- Design systém: [docs/design-system/](docs/design-system/)
- Evaluace AI: [evals/README.md](evals/README.md)
- Pravidla pro vývoj a AI agenty a kontroly: [AGENTS.md](AGENTS.md)
