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
- **Běh:** Langfuse Cloud, region EU (`https://cloud.langfuse.com`), bezplatný tarif Hobby (rozhodnuto u #5; Docker zůstává možný jen změnou `LANGFUSE_BASE_URL`). Bez nastavených klíčů je trasování vypnuté a aplikace funguje dál.
- **Tvar trace** (podle [best practices Langfuse](https://langfuse.com/docs/observability/best-practices)): jedno kolo dialogu = jeden trace s kořenem `process-message` (typ `chain`, vstup = zpráva uživatele, výstup = odpověď asistenta, metadata = návrh, revize, krok, údaje o extrakci); volání modelu jsou vnořené `generation` `extract-proposal` z integrace `langfuse.openai` s propojenou verzí promptu a metadaty `attempt`. Úvaha modelu (`reasoning` od Groq) se ukládá do metadat kořene, protože ji integrace nezachytí. Atributy: `session_id` = relace, `environment` z `LANGFUSE_TRACING_ENVIRONMENT`, `release` = verze aplikace.
- **Cena:** Langfuse ceník modelů Groq nezná, proto jsou v projektu Langfuse (Settings → Models) vlastní definice pro `openai/gpt-oss-120b`, `openai/gpt-oss-20b` a `qwen/qwen3.8-27b` s cenami z [console.groq.com/docs/models](https://console.groq.com/docs/models) (stav 23. 11. 2026, USD za 1M tokenů: 0,15/0,60; 0,075/0,30; 0,80/4,00). Reasoning tokeny se účtují cenou výstupu. Cena tokenů z cache Groq v dokumentaci uvedena není, takže se zatím počítají za 0. Při změně ceníku nebo modelu se definice v Langfuse aktualizuje.
- **Cache AI odpovědí** zůstává vlastní (lokální, klíč: vstup + model + název a verze promptu + verze schématu).
- **Evaluační sady** zůstávají v gitu (`evals/`); běhy evaluace se do Langfuse zapisují jako experimenty s odkazem na verzi promptu.

## Zvažované varianty

- **Prompty jako soubory v gitu + hash + vlastní JSONL log** — nejjednodušší a bez další služby, ale bez UI pro porovnání verzí, playgroundu a přehledu nákladů.
- **promptfoo** — silné pro porovnání promptů, ale neřeší trasování běžící aplikace.

## Důsledky

- Další služba; aplikace i testy ale musí běžet bez ní (záložní prompty, vypnuté trasování).
- Klíče Langfuse patří do `.env`, ne do repozitáře; trace nesmí obsahovat API klíče.
- Report evaluace uvádí název a verzi promptu z Langfuse.
