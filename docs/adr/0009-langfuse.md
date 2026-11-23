# ADR-0009: Langfuse pro verzování promptů a trasování AI volání

**Stav:** přijato  
**Datum:** 2026-11-23  
**Souvisí se:** ADR-0008, skill `ai-evaluace`, specifikace kap. 8

## Kontext

Potřebujeme vědět, která verze promptu a který model vytvořily daný výstup, kolik volání stojí a kde selhává extrakce. Výsledky evaluace musí být navázané na přesné znění promptu.

## Rozhodnutí

- **Prompty** se spravují v Langfuse (prompt management) s verzemi a štítky `production` a `staging`. Aplikace načítá prompt podle názvu a štítku a zaznamená číslo verze.
- **Záložní kopie** promptů je v repozitáři (`prompts/*.json`), exportovaná skriptem při každé změně štítku `production`. Aplikace ji použije, když Langfuse není dostupný; změny promptů jsou tak vidět i v PR.
- **Trasování:** každé volání AI (router, extrakce, dialog) je trace/generation v Langfuse: model, verze promptu, vstup, výstup, latence, tokeny, cena, chyba. Session v Langfuse = relace aplikace.
- **Běh:** Langfuse Cloud (bezplatný tarif) nebo lokálně v Dockeru; volba přes proměnné prostředí. Bez nastavených klíčů je trasování vypnuté a aplikace funguje dál.
- **Cache AI odpovědí** zůstává vlastní (lokální, klíč: vstup + model + název a verze promptu + verze schématu).
- **Evaluační sady** zůstávají v gitu (`evals/`); běhy evaluace se do Langfuse zapisují jako experimenty s odkazem na verzi promptu.

## Zvažované varianty

- **Prompty jako soubory v gitu + hash + vlastní JSONL log** — nejjednodušší a bez další služby, ale bez UI pro porovnání verzí, playgroundu a přehledu nákladů.
- **promptfoo** — silné pro porovnání promptů, ale neřeší trasování běžící aplikace.

## Důsledky

- Další služba; aplikace i testy ale musí běžet bez ní (záložní prompty, vypnuté trasování).
- Klíče Langfuse patří do `.env`, ne do repozitáře; trace nesmí obsahovat API klíče.
- Report evaluace uvádí název a verzi promptu z Langfuse.
