# ADR-0004: Vyměnitelný router (Jev, Layo, LLM, ruční výběr)

**Stav:** přijato; umístění portu upraveno v ADR-0006 (porty jsou v `app/`)  
**Datum:** 2026-11-23  
**Souvisí se:** specifikace kap. 6, UC-07, kap. 14

## Kontext

Router vybírá schopnost z pevné množiny. TypeSafe Jev vrací pravděpodobnosti a confidence, ale podpora češtiny není dokumentována. Aplikace musí fungovat i při výpadku API.

## Rozhodnutí

- Router je protokol `Router` v `adapters/` s jedinou metodou vracející `Ok[RoutingDecision] | Err[RoutingError]`.
- Implementace: `JevRouter` (API), `LayoRouter` (lokální open-weight varianta), `LlmRouter` (strukturovaný výstup omezený na stejné možnosti), `ManualRouter`.
- Volba implementace je v konfiguraci; `RoutingDecision` zaznamenává, která byla použita.
- Výchozí implementace se určí podle evaluace na testovací sadě (kap. 9).

## Zvažované varianty

- **Pouze Jev** — jednodušší, ale bez offline režimu a bez srovnání.
- **Pouze LLM** — jedna závislost, ale bez kalibrovaných pravděpodobností a s vyšší cenou/latencí.

## Důsledky

- Evaluační skript spouští stejnou sadu na všech dostupných implementacích.
- Údaje o Layo (lokální běh, ~0,5 GB RAM) je nutné ověřit při instalaci; dokumentace TypeSafe je neuvádí.

## Ověření v M0 (spike #7, 2026-11-23)

Doplněk k důsledkům; rozhodnutí výše se nemění. Podrobnosti a surová data v [`evals/reports/2026-11-23-router-dev-spike.md`](../../evals/reports/2026-11-23-router-dev-spike.md).

- **Jev a čeština:** na ladicí sadě 31 českých zadání (`evals/router/dev/`) volí `jev-1.14.0` druh práce správně u všech případů; nejlepší varianty otázek dávají 29/31 správných schopností. České otázky vyšly lépe než anglické nad stejným stavem. Latence medián ~150 ms, p95 ~240 ms, cena ~0,00003 USD za rozhodnutí. Jev je kandidát na výchozí implementaci; o variantě otázek a prazích rozhodne měření na `router/test` v M3.
- **Prahy:** bránou je pravděpodobnost zvolené možnosti (`probabilities[choice]`), ne `confidence`. Výchozí práh doptání 0,9, u Noulu pásmo 0,3–0,7 jako „nerozhodnuto“. Rozhodnutí o schopnosti a záměru se skládá v kódu z jednotlivých úsudků (pravdivostní tabulka v reportu).
- **Instalace:** `typesafe-sdk` (0.7.5) jako volitelná skupina závislostí `router-spike`; aplikace ani testy ho nepotřebují. Klíč `TYPESAFE_API_KEY`.
- **Layo nebylo možné ověřit:** dokumentace TypeSafe ho nezmiňuje, API ho nenabízí (`/models` vrací jen `jev-latest` a `jev-preview`) a není na PyPI, Hugging Face ani v GitHub organizaci `typesafe-ai`. Údaj „open-weight, ~0,5 GB RAM“ zůstává neověřený. `LayoRouter` se do zveřejnění modelu neimplementuje; offline provoz zajišťuje `ManualRouter` (a demo režim s připravenými odpověďmi). Úprava specifikace (UC-07, kap. 6, 11, 12, 14) čeká na rozhodnutí autora.
- **Fallback:** při chybě API se nabídne opakování a `ManualRouter`, případně `LlmRouter`; chyba volání se nikdy nevykládá jako `unclear`.
