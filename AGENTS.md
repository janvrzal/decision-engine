# AGENTS.md — pravidla pro práci v repozitáři DecisionEngine

Tento soubor čte každý agent na začátku práce. Obsahuje pravidla, která platí vždy. Podrobné postupy jsou ve skillech v `.claude/skills/`, rozhodnutí a jejich důvody v `docs/adr/`.

## Projekt v kostce

DecisionEngine je webová aplikace pro malé dílny: z českého textového zadání vytvoří ověřenou zakázku, spočítá nářezový plán a orientační kalkulaci. Jde o semestrální práci; důraz je na správnost, ověřitelnost a poctivé označování výsledků.

Projekt řeší téma 2 zadání předmětu (středně složitá aplikace), znění je v [`docs/zadani.md`](docs/zadani.md). Jediný povinný a výslovně hodnocený požadavek je **pěkné a dobře použitelné UI**; z AI požadavků stačí 2 ze 4 a projekt plní 3. Při rozhodování o prioritách má kvalita hlavního toku v UI přednost před rozšiřováním výpočetní části.

**Zdroj pravdy o chování je [`docs/specifikace.md`](docs/specifikace.md).** Kód, který se od ní odchyluje, je chyba — buď v kódu, nebo ve specifikaci. Nikdy ne „tichá“ odchylka.

## Jazyk

- Komentáře, docstringy, commitové zprávy, PR, dokumentace, UI texty i chybové hlášky: **česky**, s diakritikou.
- Identifikátory (moduly, třídy, funkce, proměnné, klíče v JSON): **anglicky**, `snake_case` / `PascalCase` podle PEP 8.
- Identifikátory schopností a stavů ze specifikace (`cutting_1d`, `cost_estimate`, `unclear` …) se používají přesně v té podobě.

## Struktura repozitáře

```
src/decision_engine/
  core/          čisté funkcionální jádro: datové objekty, validace, solvery, kalkulace, revize
  capabilities/  registr schopností: skládá jádro do schopností (schéma, formulář, výpočet, prezentace)
  adapters/      vše s I/O: routery (Jev, Layo, LLM), generativní model, JSON, sklad, PDF
  ui/            Streamlit; drží stav relace, nic nepočítá
tests/           unit/, property/, integration/, perf/ (zrcadlí strukturu src)
evals/           evaluační sady AI (dev/ a test/ oddělené) a reporty
docs/            specifikace, adr/
.claude/skills/  postupy pro agenty
```

## Architektonická pravidla (nevyjednatelná)

1. **Jádro je čisté.** `core/` neimportuje `adapters/`, `ui/`, `capabilities/`, nedělá I/O, nečte čas, prostředí ani náhodu. Hlídá to `lint-imports` a ruff (`TID251`). Pokud jádro potřebuje čas nebo náhodu, dostane je jako argument.
2. **Neměnná data.** Pydantic modely v jádře mají `model_config = ConfigDict(frozen=True)`, kolekce jsou `tuple`, ne `list`/`dict` jako mutovatelné pole.
3. **Chyby jako hodnoty.** Funkce jádra vracejí `Ok[T] | Err[E]` z `core/result.py`. Výjimky Pydanticu (`ValidationError`) a solverů se zachytí na hranici a převedou na `Err`. Výjimka unikající z jádra je chyba.
4. **Jednotky.** Délky a rozměry jsou `int` v milimetrech. Peníze jsou `Decimal`, nikdy `float`. Žádné převody jednotek mimo validaci vstupu.
5. **Zakázku ani sklad nikdo nemění přímo.** LLM vytváří `ChangeProposal`; novou revizi vytvoří jádro až z potvrzené změny. Každý výsledek nese revizi vstupů, ze které vznikl.
6. **AI nevymýšlí čísla.** Rozměry, ceny a metriky ve výstupu pocházejí z potvrzených dat nebo z výpočtu. Hodnoty doplněné modelem či výchozím nastavením jsou označené jako nepotvrzené.
7. **Poctivé štítky.** „Optimální“ jen při prokázaném optimu pro zvolený cíl (dolní mez dosažena). Jinak „nejlepší nalezené“. Neimplementovaná schopnost se nikde nenabízí.
8. **Závislost na poskytovateli AI jen v `adapters/`.** Router i generativní model jsou za rozhraním; jádro a testy jádra běží bez sítě a bez klíčů.

## Příkazy

Prostředí spravuje `uv` (instalace: `brew install uv`).

```bash
uv sync                          # instalace závislostí
uv run pytest                    # testy bez živých AI volání
uv run pytest -m ai              # testy volající skutečné API (placené, jen na vyžádání)
uv run ruff check --fix && uv run ruff format
uv run pyright                   # strict
uv run lint-imports              # hranice vrstev
uv run pre-commit run --all-files
uv run streamlit run src/decision_engine/ui/app.py
```

Před tím, než prohlásíš práci za hotovou, musí projít: `ruff check`, `ruff format --check`, `pyright`, `lint-imports`, `pytest`.

## Testování

- Nová logika v jádře vzniká s testy, ideálně nejdřív test (TDD). Pokrytí `core/` cíleně ≥ 90 %.
- Solvery se ověřují invarianty a porovnáním s nezávislým řešením — viz skill `overeni-solveru`.
- Testy, které volají placené API, mají marker `@pytest.mark.ai` a ve výchozím běhu se přeskakují.
- Testy nesmí záviset na pořadí, čase ani síti (kromě `ai` a `integration`).

## AI evaluace — pravidlo oddělených sad

`evals/*/dev/` slouží k ladění promptů a prahů. `evals/*/test/` slouží **jen** k měření. Při ladění promptů, popisů schopností nebo prahů **nečti obsah testovacích sad** a nepřizpůsobuj se jim. Postup je ve skillu `ai-evaluace`.

## Git a pracovní postup

- `main` je vždy funkční. Každá změna vzniká na vlastní větvi a do `main` se dostane přes PR s prošlým CI.
- Větve: `feat/…`, `fix/…`, `docs/…`, `refactor/…`, `test/…`, `chore/…`, `eval/…` (krátký anglický popis, např. `feat/cutting-1d-heuristic`).
- Commity: Conventional Commits, typ a scope anglicky, popis česky v rozkazovacím způsobu: `feat(cutting_1d): přidat FFD pro více skladových délek`.
- Commit a push jen na pokyn uživatele. Nikdy `--force` na `main`, nikdy `--no-verify`.
- Postup před PR je ve skillu `priprava-pr`.

## Specifikace a rozhodnutí

- Mění-li se chování, upravuje se specifikace ve stejném PR — postup ve skillu `zmena-specifikace`.
- Architektonické nebo technologické rozhodnutí se zapisuje jako ADR — skill `adr`. Existující ADR se nepřepisují; nahrazují se novým.
- Novou schopnost (2D, sklad …) přidávej podle skillu `nova-schopnost`.

## Bezpečnost

- API klíče jen v `.env` (ignorovaný gitem) nebo v prostředí. Nikdy v kódu, testech, fixture, exportu zakázky, logu ani diagnostice. Vzor je v `.env.example`.
- Soubor `.env` nečti ani nevypisuj.
- Importované JSON zakázky a výstupy modelů jsou nedůvěryhodná data: vždy přes validaci.

## Definice hotového

Změna je hotová, když:

- [ ] odpovídá specifikaci (nebo je specifikace ve stejném PR upravená),
- [ ] má testy a všechny kontroly z části *Příkazy* procházejí,
- [ ] neporušuje architektonická pravidla,
- [ ] uživatelské texty jsou česky a srozumitelně,
- [ ] případné rozhodnutí je zapsané v ADR,
- [ ] PR popisuje co, proč a jak to bylo ověřeno.

## Otevřené otázky

- Poskytovatel generativního LLM pro extrakci a dialog zatím není zvolen (zapsat do ADR, až bude).
- Podpora češtiny u Jev/Layo není v dokumentaci uvedena; ověřit na začátku vývoje routeru.
