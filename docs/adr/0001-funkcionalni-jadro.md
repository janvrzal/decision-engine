# ADR-0001: Funkcionální jádro, imperativní obal a chyby jako hodnoty

**Stav:** přijato; rozdělení vrstev rozšířeno v ADR-0006  
**Datum:** 2026-11-23  
**Souvisí se:** specifikace kap. 7

## Kontext

Aplikace kombinuje nedeterministické AI volání, uživatelský stav ve Streamlitu a výpočty, u kterých požadujeme ověřitelnou správnost. Výpadek AI nesmí zablokovat výpočet (UC-07) a jádro musí jít testovat bez sítě a klíčů.

## Rozhodnutí

- Kód je rozdělen na `core/` (čisté funkce, neměnná data), `capabilities/` (registr), `adapters/` (veškeré I/O a poskytovatelé AI) a `ui/` (Streamlit).
- `core/` nesmí importovat ostatní vrstvy ani knihovny s I/O; nesmí číst čas, prostředí ani náhodu.
- Datové objekty jsou Pydantic modely s `frozen=True` a kolekcemi typu `tuple`.
- Funkce jádra vracejí `Ok[T] | Err[E]` (vlastní malé typy v `core/result.py`). Výjimky Pydanticu a OR-Tools se zachytí na hranici a převedou na `Err` se seznamem chyb po polích.

## Zvažované varianty

- **Výjimky všude** — jednodušší zápis, ale chyby validace nejsou vidět v typech a snadno uniknou do UI.
- **Knihovna `returns`/`result`** — hotové typy, ale další závislost a horší čitelnost pro hodnotitele; vlastních ~40 řádků stačí.

## Důsledky

- Hranice vrstev hlídá `import-linter` (`uv run lint-imports`), zákaz `random`, `datetime.now`, `time.time`, `os.environ` v jádře hlídá ruff `TID251`.
- Chyby polí lze zobrazit přímo v kontrolní tabulce.
- Mírně delší kód kolem volání Pydanticu (obal `parse`).
