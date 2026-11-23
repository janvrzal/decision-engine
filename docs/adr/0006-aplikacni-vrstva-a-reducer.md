# ADR-0006: Aplikační vrstva, stav jako reducer a webové API

**Stav:** přijato  
**Datum:** 2026-11-23  
**Souvisí se:** ADR-0001 (rozšiřuje rozdělení vrstev), ADR-0007, specifikace kap. 7

## Kontext

Jeden tah uživatele („Přidej dvě příčky po 850 mm“) prochází routerem, extrakcí, validací, potvrzením, novou revizí, výpočtem a kalkulací. Jádro nesmí volat síť a UI nemá nic počítat, takže řízení toku dosud nemělo kde žít. Pravidla jako „nepotvrzený návrh nepřepíše data“ nebo „starý výsledek je neaktuální“ mají být vynucená kódem, ne disciplínou. UI je samostatná webová aplikace (ADR-0007), takže backend musí nabízet API.

## Rozhodnutí

Vrstvy v Python balíčku `decision_engine`:

| Vrstva | Obsah | Smí importovat |
|---|---|---|
| `core/` | Datové objekty, validace, solvery, kalkulace, **stav aplikace, události a reducer** | nic z ostatních vrstev |
| `capabilities/` | Registr schopností | `core` |
| `app/` | Případy užití: smyčka událostí a efektů, **porty** (`Protocol`) pro adaptéry | `core`, `capabilities` |
| `adapters/` | Implementace portů: Groq/LLM, Jev, Layo, Langfuse, úložiště, PDF | `core`, `app` (jen porty) |
| `api/` | FastAPI: HTTP endpointy, serializace, sestavení závislostí (composition root) | vše výše |

**Stav jako reducer.** Stav relace je jeden neměnný objekt `AppState`. Vše, co se může stát, je typovaná událost (`MessageSent`, `ProposalReceived`, `ProposalConfirmed`, `SolveRequested`, `SolveFinished`, `AiFailed` …). Čistá funkce

```python
def reduce(state: AppState, event: Event) -> tuple[AppState, tuple[Effect, ...]]
```

vrátí nový stav a seznam efektů (popisů vedlejších účinků, např. `CallExtractor(...)`, `RunSolver(...)`). Efekty vykoná `app/` přes porty a jejich výsledek vrátí jako novou událost.

**API.** Frontend posílá události (`POST /api/sessions/{id}/events`) a dostává zpět pohled na stav (view model). Stav relací drží backend v paměti; aplikace běží lokálně pro jednoho uživatele. Frontend nic nepočítá a nerozhoduje o přechodech stavu.

## Zvažované varianty

- **Logika v UI/callbacích** — nejrychlejší začátek, ale netestovatelná a při změně UI se přepisuje.
- **Služby bez explicitního stavu** (`app/` mění objekty na místě) — méně formální, ale stavy zakázky jsou implicitní a pravidla specifikace se hlídají jen testy jednotlivých míst.
- **Stav na frontendu** (frontend drží zakázku a backend je bezstavový) — logika by se rozdělila mezi dva jazyky.

## Důsledky

- Dialogové scénáře z kap. 9 jsou jednotkové testy: sled událostí → očekávaný stav.
- Tok s AI se testuje s falešnými adaptéry (`FakeExtractor`, `FakeRouter`) bez sítě.
- Výměna UI se nedotkne logiky.
- Každá akce potřebuje typ události a větev v `reduce`; očekáváme 10–20 událostí.
- Hranice vrstev hlídá `import-linter`.
