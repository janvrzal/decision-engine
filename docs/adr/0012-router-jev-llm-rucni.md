# ADR-0012: Router s implementacemi Jev, LLM a ruční; Layo vyřazeno

**Stav:** přijato  
**Datum:** 2026-11-24  
**Souvisí se:** specifikace kap. 6 (Router), UC-05, UC-07, kap. 9, 12; částečně nahrazuje ADR-0004 (implementace `LayoRouter`); Issues #53, #56

## Kontext

ADR-0004 zavedl vyměnitelný router za portem `Router` se čtyřmi implementacemi. Spike #7 potvrdil, že Jev zvládá česká zadání (29/31 na dev sadě), ale lokální varianta Layo veřejně dostupná není (dokumentace, API ani balíček). Specifikace s ní přitom počítala pro offline provoz, demo a scénář obhajoby. Hromadná recenze (Issue #56) to označila jako nesplnitelný slib. Autor rozhodl, že roli Layo převezme Jev od TypeSafe a router bude mít tři implementace.

## Rozhodnutí

- Port `Router` v `app/ports.py` vrací `Result[RoutingDecision, RoutingError]`. `RoutingDecision` je v jádře: výsledek (`supported` / `unclear` / `unsupported`), schopnost, záměr, případná doptávací otázka a název implementace.
- Implementace v `adapters/`:
  - `JevRouter` — TypeSafe Jev (System One), otázky typu Choice a Noul převzaté ze spiku, rozhodnutí podle `probabilities` s prahem 0,9 (ADR-0004, dodatek ze spiku).
  - `LlmRouter` — generativní model (Groq) s výstupem omezeným na stejnou množinu možností a s doptávací otázkou; prompt `route-request` ve správě promptů.
  - `ManualRouter` — bez klasifikace, zprávu předá jediné implementované schopnosti; vždy dostupný.
- Výchozí volba podle konfigurace: Jev, je-li klíč TypeSafe; jinak LLM, je-li klíč LLM; jinak ruční. Proměnná `ROUTER` volbu přepíše.
- Chyba API routeru se nikdy nevykládá jako `unclear`: aplikace zkusí další implementaci v pořadí Jev → LLM → ruční a záložní postup zapíše do trace.
- `LayoRouter` se neimplementuje. Offline provoz zajišťuje `ManualRouter`, ruční zadání a demo s připravenými odpověďmi.

## Zvažované varianty

- **Ponechat Layo ve specifikaci do jeho zveřejnění** — specifikace by slibovala něco, co nejde předvést; porušuje to zásadu poctivých štítků.
- **Nahradit Layo jiným lokálním modelem (Ollama)** — další závislost a instalace, kvalita v češtině neověřená; pro semestrální rozsah nepřiměřené.
- **Jen LLM router** — jednodušší, ale nevyužije změřený Jev a scénář obhajoby přijde o srovnání implementací.

## Důsledky

- Specifikace, service design a AGENTS.md už Layo nezmiňují; otevřená otázka v AGENTS.md je uzavřená.
- Testy a běh bez sítě používají falešný router nebo `ManualRouter`; žádný test nepotřebuje klíč TypeSafe.
- Volbu výchozího routeru a prahu určí měření na `evals/router/test` (spustí autor, placená API).
- Přehodnotit, pokud TypeSafe Layo zveřejní: přibude čtvrtá implementace za stejným portem.
