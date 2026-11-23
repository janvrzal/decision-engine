# Zadání semestrální práce

Projekt DecisionEngine řeší **téma 2: Vytvoření středně složité aplikace**. Ostatní témata předmětu (agent, bias, syntetická data, RAG) se projektu netýkají.

## Znění zadání (téma 2)

> Aplikace musí mít vlastní uživatelské rozhraní, se kterým si vyhrajete, aby vypadalo pěkně a bylo dobře použitelné. Stačí Streamlit, Gradio nebo jednoduchá webová stránka – důraz je na použitelnost a vizuální čistotu, ne na technologický stack.
>
> Požadavky, nutno splnit alespoň 2 ze 4:
>
> - strukturovaný výstup / function calling (Cv. 6, slide 17)
> - vícekolový dialog s pamětí kontextu, nebo kombinace více LLM volání s různou rolí
> - propojení LLM s dalším datovým zdrojem (vlastní data, web search, výpočet, parsing dokumentu/obrázku)
> - multimodalita – vstup obrázku, PDF, audia (např. analýza faktury, popis fotky, přepis nahrávky)
>
> Rozdíl vnímání aplikace vs agent: Aplikace má UI a uživatele, který s ní interaktivně pracuje – klikne, něco zadá, dostane výstup, reaguje na něj. Agent oproti tomu běží na pozadí na trigger a uživatel s ním přímo neinteraguje.
>
> Příklady aplikací s plným bodovým score z minulého semestru: Finanční plánovač s GPT, Email verifier (ověřovač, zda je existující mailový účet fake, nebo ne), aplikace vizualizující data pro diabetiky...

## Co z toho plyne pro projekt

| Požadavek | Povinnost | Jak ho DecisionEngine splňuje | Kde ve specifikaci |
|---|---|---|---|
| Vlastní UI, pěkné a dobře použitelné | **povinné, hodnocené** | Webové UI (FastAPI + SvelteKit, ADR-0007); tři kroky zakázky, editovatelné tabulky, měřítkový plán, navržené stavy a chyby | kap. 4, 9 |
| Strukturovaný výstup / function calling | 1 z 2+ | LLM extrakce do validovaného schématu; router vrací typovanou volbu | kap. 6, 7 |
| Vícekolový dialog s pamětí / více LLM rolí | 1 z 2+ | Navazující změny zakázky nad potvrzenou revizí; router + extrakce + doptávání jako různé role | UC-03, kap. 6 |
| Propojení LLM s datovým zdrojem | 1 z 2+ | Výpočet nářezového plánu a kalkulace; u rozšíření sklad jako vlastní data | UC-01, UC-04, UC-08 |
| Multimodalita | nevyužito | Mimo rozsah semestru | kap. 3, 13 |

Splněny jsou 3 ze 4 volitelných požadavků (stačí 2), takže výpadek jednoho z nich hodnocení neohrozí.

## Priority vyplývající ze zadání

1. **UI je jediný povinný požadavek a výslovně se hodnotí** („vyhrát si“, „pěkně“, „použitelnost a vizuální čistota“). Má přednost před rozšiřováním výpočetní části.
2. Hodnotitel aplikaci zkouší interaktivně: zadá, dostane výstup, reaguje. Hlavní tok (zadání → kontrola → plán a cena → úprava dialogem) musí být plynulý a bez slepých míst.
3. Hloubka optimalizace (dolní meze, CP-SAT, 2D, sklad) je přidaná hodnota, ne požadavek zadání.
