# AGENTS.md — pravidla pro práci v repozitáři DecisionEngine

Tento soubor čte každý agent na začátku práce. Obsahuje pravidla, která platí vždy. Podrobné postupy jsou ve skillech v `.claude/skills/`, rozhodnutí a jejich důvody v `docs/adr/`.

## Projekt v kostce

DecisionEngine je lokálně spouštěná webová aplikace pro malé dílny: z českého textového zadání vytvoří ověřenou zakázku, spočítá nářezový plán a orientační kalkulaci. Jde o semestrální práci; důraz je na správnost, ověřitelnost, poctivé označování výsledků a kvalitní UI.

Projekt řeší téma 2 zadání předmětu (středně složitá aplikace), znění je v [`docs/zadani.md`](docs/zadani.md). Jediný povinný a výslovně hodnocený požadavek je **pěkné a dobře použitelné UI**; z AI požadavků stačí 2 ze 4 a projekt plní 3. Při rozhodování o prioritách má kvalita hlavního toku v UI přednost před rozšiřováním výpočetní části.

**Zdroj pravdy o chování je [`docs/specifikace.md`](docs/specifikace.md).** Kód, který se od ní odchyluje, je chyba — buď v kódu, nebo ve specifikaci. Nikdy ne „tichá“ odchylka.

## Jazyk

- Komentáře, docstringy, commitové zprávy, PR, dokumentace, UI texty i chybové hlášky: **česky**, s diakritikou.
- Identifikátory v Pythonu i TypeScriptu (moduly, třídy, funkce, proměnné, klíče v JSON, endpointy): **anglicky**.
- Identifikátory schopností, událostí a stavů ze specifikace (`cutting_1d`, `ProposalConfirmed`, `unclear` …) se používají přesně v té podobě.

## Struktura repozitáře

```
src/decision_engine/
  core/          čisté jádro: datové objekty, validace, solvery, kalkulace, revize,
                 stav relace, události, reducer, vykreslení plánu do SVG
  capabilities/  registr schopností
  app/           případy užití: smyčka událostí a efektů, porty (Protocol) pro adaptéry
  adapters/      implementace portů: Groq/LLM, Jev (TypeSafe), Langfuse, úložiště, PDF
  api/           FastAPI: endpointy, serializace, sestavení závislostí, servírování frontendu
frontend/        SvelteKit (Svelte 5, TypeScript) jako SPA
tests/           unit/, property/, flow/, integration/, perf/
evals/           evaluační sady AI (dev/ a test/ oddělené) a reporty
prompts/         záložní kopie promptů exportovaná z Langfuse
docs/            specifikace, zadání, adr/
.claude/skills/  postupy pro agenty
```

## Architektonická pravidla (nevyjednatelná)

1. **Jádro je čisté.** `core/` neimportuje ostatní vrstvy, nedělá I/O, nečte čas, prostředí ani náhodu. Hlídá to `lint-imports` a ruff (`TID251`). Potřebuje-li jádro čas nebo náhodu, dostane je jako argument.
2. **Směr závislostí:** `api → app/adapters → capabilities → core`; adaptéry znají z `app/` jen porty. Žádná vrstva neimportuje `api/`.
3. **Neměnná data.** Pydantic modely v jádře mají `frozen=True`, kolekce jsou `tuple`.
4. **Chyby jako hodnoty.** Funkce jádra a portů vracejí `Ok[T] | Err[E]` z `core/result.py`. Výjimky knihoven (Pydantic, OR-Tools, HTTP klienti) se zachytí na hranici a převedou na `Err`.
5. **Stav mění jen reducer.** Stav relace je `AppState`; mění ho jen `reduce(state, event)`, který vrací nový stav a efekty. Efekty vykonává `app/`. Odvozené vlastnosti (např. neaktuální výsledek) se počítají, neukládají.
6. **Jednotky.** Délky a rozměry jsou `int` v milimetrech, peníze `Decimal`, nikdy `float`.
7. **Zakázku ani sklad nikdo nemění přímo.** LLM vytváří `ChangeProposal`; novou revizi vytvoří jádro až z potvrzené změny. Každý výsledek nese revizi vstupů.
8. **AI nevymýšlí čísla.** Rozměry, ceny a metriky ve výstupu pocházejí z potvrzených dat nebo z výpočtu. Hodnoty doplněné modelem či výchozím nastavením jsou označené jako nepotvrzené.
9. **Poctivé štítky.** „Optimální“ jen při prokázaném optimu pro zvolený cíl. Neimplementovaná schopnost se nikde nenabízí.
10. **Frontend je tenký.** Zobrazuje view model, posílá události, formátuje čísla a jednotky (`cs-CZ`). Nepočítá metriky, ceny ani přechody stavu. Typy API se generují z OpenAPI, nepíší se ručně.
11. **Poskytovatelé AI jen v `adapters/`.** Aplikace i testy musí běžet bez sítě, bez klíčů a bez Langfuse (falešné adaptéry, záložní prompty).

## Styl kódu

- `core/` funkcionálně: neměnná data a samostatné funkce v modulech, žádné třídy s chováním, `match` nad `Ok`/`Err` a událostmi.
- `app/` imperativně: čitelný procedurální kód smyčky efektů.
- `adapters/` jako třídy implementující `Protocol`; skládání, **žádná dědičnost**.
- Moduly cíleně do ~300 řádků, jedna odpovědnost. Registr schopností je statický seznam.

## Příkazy

Backend (`uv`: `brew install uv`):

```bash
uv sync
uv run pytest                    # bez živých AI volání
uv run --env-file .env pytest -m ai   # placená API, jen na vyžádání
uv run ruff check --fix && uv run ruff format
uv run pyright                   # strict
uv run lint-imports              # hranice vrstev
uv run decision-engine           # spustí aplikaci (API + sestavený frontend)
uv run --env-file .env python scripts/trace_turn.py  # jedno kolo extrakce s AI a trasováním
uv run --env-file .env python scripts/prompts.py export  # záložní kopie promptů z Langfuse
```

Frontend (`pnpm`: `brew install pnpm`), ve složce `frontend/`:

```bash
pnpm install
pnpm dev                         # vývojový server s proxy na backend
pnpm generate:api                # typy klienta z OpenAPI backendu
pnpm check                       # svelte-check + TypeScript
pnpm lint && pnpm format
pnpm test                        # Vitest
pnpm test:e2e                    # Playwright, hlavní tok
```

Před tím, než prohlásíš práci za hotovou, musí projít kontroly vrstvy, které se změna týká (backend: ruff, pyright, lint-imports, pytest; frontend: check, lint, test, u změn toku i test:e2e).

## Testování

- Jádro: TDD, jednotkové a property testy (`hypothesis`); pokrytí `core/` cíleně ≥ 90 %.
- Reducer a tok: `tests/flow/` — sled událostí → očekávaný stav, s falešnými adaptéry.
- Solvery: skill `overeni-solveru`.
- Frontend: Vitest pro logiku komponent, Playwright pro hlavní tok, axe pro přístupnost.
- Testy volající placené API mají marker `@pytest.mark.ai` a ve výchozím běhu se přeskakují.

## AI: prompty, trasování, evaluace

- Prompty se spravují v Langfuse (štítky `production`, `staging`); záložní kopie v `prompts/` se exportuje při změně `production`. Prompt nepiš natvrdo do kódu.
- Každé volání AI se trasuje přes adaptér Langfuse; trace nesmí obsahovat klíče.
- `evals/*/dev/` slouží k ladění, `evals/*/test/` **jen** k měření. Při ladění promptů, popisů schopností nebo prahů **nečti obsah testovacích sad**. Postup ve skillu `ai-evaluace`.

## UI

Zásady kvality jsou ve specifikaci (kap. 4) a kritéria v kap. 9. Postup a konvence frontendu jsou ve skillu `ui-frontend`. Změnu UI vždy ověř v běžící aplikaci, ne jen testy.

## Git a pracovní postup

- Práce postupuje svislými řezy (milníky v kap. 11 specifikace); úkoly jsou GitHub Issues v příslušném milníku.
- `main` je vždy funkční. Každá změna na vlastní větvi, do `main` přes PR s prošlým CI. Slučuje uživatel.
- Větve: `feat/…`, `fix/…`, `docs/…`, `refactor/…`, `test/…`, `chore/…`, `eval/…`.
- Commity: Conventional Commits, typ a scope anglicky, popis česky v rozkazovacím způsobu: `feat(cutting_1d): přidat FFD pro více skladových délek`.
- Commit a push jen na pokyn uživatele. Nikdy `--force` na `main`, nikdy `--no-verify`.
- Postup před PR je ve skillu `priprava-pr`.

## Specifikace a rozhodnutí

- Mění-li se chování, upravuje se specifikace ve stejném PR — skill `zmena-specifikace`.
- Architektonické nebo technologické rozhodnutí se zapisuje jako ADR — skill `adr`.
- Novou schopnost přidávej podle skillu `nova-schopnost`.

## Bezpečnost

- Klíče (Groq, TypeSafe, Langfuse) jen v `.env` (ignorovaný gitem) nebo v prostředí. Nikdy v kódu, testech, fixture, exportu zakázky, logu, trace ani na frontendu. Vzor je v `.env.example`.
- Soubor `.env` nečti ani nevypisuj. Repozitář je veřejný.
- Importované JSON zakázky, požadavky na API a výstupy modelů jsou nedůvěryhodná data: vždy přes validaci.

## Definice hotového

- [ ] odpovídá specifikaci (nebo je specifikace ve stejném PR upravená),
- [ ] má testy a kontroly z části *Příkazy* procházejí,
- [ ] neporušuje architektonická pravidla,
- [ ] změna UI je ověřená v běžící aplikaci a splňuje checklist ze skillu `ui-frontend`,
- [ ] uživatelské texty jsou česky a srozumitelně,
- [ ] případné rozhodnutí je zapsané v ADR,
- [ ] PR popisuje co, proč a jak to bylo ověřeno.

## Otevřené otázky

- Jev zvládá česká zadání (spike #7, ADR-0004); variantu otázek a prahy routeru určí měření na `router/test` v M3.
