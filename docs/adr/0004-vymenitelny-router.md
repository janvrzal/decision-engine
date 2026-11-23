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
