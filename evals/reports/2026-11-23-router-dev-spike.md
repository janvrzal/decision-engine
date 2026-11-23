# Spike #7: Jev a Layo pro router — čeština, instalace, latence

**Datum:** 2026-11-23
**Sada:** `evals/router/dev/cases.json` (31 případů, **dev** — ladicí, ne měřicí sada; `evals/router/test/` se nečetla ani nepoužila)
**Implementace:** Jev přes API (prototyp `scripts/spike_router.py`, ne produkční `JevRouter`); Layo nebylo k dispozici (viz níže)
**Model:** `jev-1.14.0` (vrácený API v každé odpovědi), SDK `typesafe-sdk` 0.7.5
**Prompt / schéma:** otázky Jev jsou ve skriptu (spike, mimo Langfuse); verze schématu není — produkční `RoutingDecision` vznikne v M3
**Surová data:** `evals/reports/raw/2026-11-23-router-dev-spike.jsonl` (payload každého požadavku, pravděpodobnosti, latence, tokeny; metriky jdou přepočítat přes `--from-raw` bez API)

> Metriky platí jen pro tuto malou ladicí sadu a uvedené podmínky. Nejsou obecnou zárukou přesnosti a nenahrazují měření na oddělené sadě `router/test` (≥ 50 případů, spec kap. 9) v M3.

## Shrnutí

1. **Jev češtinu zvládá.** Otázky i stav v češtině, zadání s hovorovými výrazy, bez diakritiky i s jednotkami v cm: samotná volba druhu práce (`task`) byla správně u 31/31 případů, většinou s pravděpodobností ≥ 0,9. Česky psané otázky vyšly o něco lépe než anglické nad stejným českým stavem (81 % vs. 77 % u téže pravdivostní tabulky).
2. **Nejlepší varianty mají na dev sadě 29/31 (94 %)** — jednoduchá Choice přímo nad množinou ze specifikace (`naive_cs`) i rozložené otázky s rozhodnutím v kódu (`decomposed_cs_v2`). Druhá varianta vznikla laděním na této sadě, takže její výsledek je optimistický.
3. **Latence:** medián ~150 ms, p95 ~240 ms na jedno volání (2–3 otázky), první volání ~235 ms včetně TLS. Import SDK ~0,24 s.
4. **Cena:** 155 volání, 119 071 vstupních tokenů ≈ **0,005 USD** celkem (~770 tokenů a ~0,00003 USD na jedno rozhodnutí routeru).
5. **Layo není dostupné.** Dokumentace TypeSafe ho nezmiňuje, API ho nenabízí (`/models` vrací jen `jev-latest` a `jev-preview`), na PyPI, Hugging Face ani v GitHub organizaci `typesafe-ai` není. Údaj „open-weight, ~0,5 GB RAM“ ze specifikace se nepodařilo ověřit. Offline routing proto zatím zajistí jen `ManualRouter`.

## Instalace a spuštění

| Položka | Jev | Layo |
|---|---|---|
| Balíček | `typesafe-sdk` (PyPI, 0.7.5; závisí na `httpx2`, `pydantic`, `tenacity`) | nenalezen |
| Instalace | `uv sync --group router-spike` (< 1 s z cache), volitelná skupina, aplikace a testy ji nepotřebují | — |
| Klíč | `TYPESAFE_API_KEY` (už je v `.env.example`) | — |
| Start | import SDK ~0,24 s; první volání ~235 ms | — |
| Offline | ne (vzdálené API `https://api.typesafe.ai`) | nelze ověřit |
| Modely | `jev-latest` → `jev-1.14.0`; `jev-preview` (teď totéž) | — |

Dokumentace (stav 23. 11. 2026) k jazykům uvádí jen „Better multilingual support“ v changelogu Jev 1.14, seznam jazyků ani češtinu nezmiňuje. Rate limity se nastavují v konzoli, čísla v dokumentaci nejsou; SDK opakuje `429` podle `retry-after` (ve skriptu omezeno na 2 opakování).

## Sada

31 ručně psaných českých zadání, rozložení podle očekávané schopnosti:

| Schopnost | Počet | Z toho s rozpracovanou zakázkou |
|---|---|---|
| `cutting_1d` | 17 | 7 (5 změn, 2 dotazy k výsledku) |
| `cost_estimate` | 5 | 3 |
| `unclear` | 4 | 0 |
| `unsupported` | 5 | 0 |

Štítky: `bez_diakritiky`, `slang`, `jednotky_cm`, `vice_delek`, `odkaz` („ty příčky“), `hranicni`, `2d` (`cutting_2d` není implementované, proto `unsupported`) aj. Záměr (`new_order`, `change_order`, `result_question`) se hodnotí jen u 10 případů s rozpracovanou zakázkou; bez zakázky je záměr vždy nová zakázka a rozhoduje ho kód.

Stav posílaný Jev: `{"zprava": …, "rozpracovana_zakazka": <díly, skladové délky, prořez, stav plánu> | "žádná – uživatel zatím nic nezadal"}`.

## Varianty otázek

| Varianta | Otázky | Rozhodnutí v kódu |
|---|---|---|
| `naive_cs` | Choice `capability` přímo nad `cutting_1d`, `cost_estimate`, `unclear`, `unsupported`; Choice `intent` | hlavní volba; pravděpodobnost < 0,5 → `unclear` |
| `decomposed_cs` | Choice `task` (`cutting_bars`, `pricing`, `cutting_sheets`, `packing`, `other_request`); Noul `concrete` („je jasné, co spočítat?“); Choice `intent` | `concrete` < 0,7 nebo `task` < 0,5 → `unclear`, jinak mapování `task` → schopnost |
| `decomposed_cs_reversed` | totéž s obráceným pořadím možností | totéž |
| `decomposed_en` | totéž, otázky a kritéria anglicky (stav česky) | totéž |
| `decomposed_cs_v2` | jako `decomposed_cs`, Noul `concrete` přeformulovaný nezávisle na tom, zda úlohu aplikace umí | pravdivostní tabulka níže |

Pravdivostní tabulka `decomposed_cs_v2` (`task` < 0,5 → vždy `unclear`):

| `task` | `concrete` ≥ 0,7 | 0,3–0,7 | < 0,3 |
|---|---|---|---|
| `cutting_bars` | `cutting_1d` | `cutting_1d` | `unclear` |
| `pricing` | `cost_estimate` | `cost_estimate` | `cost_estimate` |
| `cutting_sheets`, `packing` | `unsupported` | `unsupported` | `unsupported` |
| `other_request` | `unsupported` | `unclear` | `unclear` |

Důvod: u řezání chybějící údaje dohledá extrakce podle schématu a u ceny bez plánu aplikace nabídne nejdřív plán (spec kap. 6), takže Noul má rozhodovat hlavně „nejasné × mimo rozsah“.

## Výsledky

| Varianta | Schopnost | Záměr (10 se zakázkou) | Latence medián / p95 | Vstupní tokeny / volání |
|---|---|---|---|---|
| `naive_cs` | 29/31 (94 %) | 9/10 | 147 / 237 ms | 624 |
| `decomposed_cs` | 25/31 (81 %) | 9/10 | 150 / 188 ms | 840 |
| `decomposed_cs_reversed` | 25/31 (81 %) | 9/10 | 153 / 233 ms | 840 |
| `decomposed_en` | 24/31 (77 %) | 9/10 | 145 / 221 ms | 692 |
| `decomposed_cs_v2` | 29/31 (94 %) | 9/10 | 148 / 240 ms | 847 |

Latence je měřená ze stroje autora (macOS, domácí připojení), sekvenčně, jedno volání = jeden požadavek se všemi otázkami varianty; první volání každého běhu (studené spojení) je z mediánu vyřazené.

### Kalibrace

Přesnost schopnosti podle pravděpodobnosti hlavní volby (`capability`, resp. `task`):

| Varianta | ≥ 0,9 | 0,7–0,9 | < 0,7 |
|---|---|---|---|
| `naive_cs` | 29/29 | 0/1 | 0/1 |
| `decomposed_cs` | 23/29 | 1/1 | 1/1 |
| `decomposed_cs_v2` | 28/29 | 1/1 | 0/1 |

U `naive_cs` jsou obě chyby právě v případech s pravděpodobností pod 0,9, takže práh doptání **0,9** na pravděpodobnost zvolené možnosti by je na této sadě zachytil (u `decomposed_*` se chyby rodí v Noulu, ne v `task`). Podle dokumentace TypeSafe má u Choice smysl prahovat `probabilities[choice]`, ne `confidence` (ta je z ní odvozená). Na 31 případech je to jen orientace; práh se stanoví v M3 na větší sadě.

### Matice záměn (řádek = očekáváno, sloupec = vyšlo)

`naive_cs`

| | cutting_1d | cost_estimate | unclear | unsupported |
|---|---|---|---|---|
| cutting_1d | 17 | 0 | 0 | 0 |
| cost_estimate | 0 | 5 | 0 | 0 |
| unclear | 1 | 0 | 2 | 1 |
| unsupported | 0 | 0 | 0 | 5 |

`decomposed_cs_v2`

| | cutting_1d | cost_estimate | unclear | unsupported |
|---|---|---|---|---|
| cutting_1d | 16 | 0 | 1 | 0 |
| cost_estimate | 0 | 5 | 0 | 0 |
| unclear | 1 | 0 | 3 | 0 |
| unsupported | 0 | 0 | 0 | 5 |

`decomposed_cs` (1. iterace): 2× `cutting_1d` → `unclear`, 1× `cost_estimate` → `unclear`, 3× `unsupported` → `unclear`; `unclear` 4/4.

### Chybné případy

- **router-dev-024 „Potřebuju něco nařezat.“** (`unclear`): `naive_cs` → `cutting_1d` (0,59 vs. `unclear` 0,40); `v2` → `cutting_1d` (`task` 0,58, `concrete` přesně 0,30 na hraně prahu). Hraniční případ — router řezání pozná správně, chybí díly; v aplikaci by se na ně stejně doptala extrakce. Obě varianty mají pravděpodobnost < 0,9, takže by je zachytil práh doptání.
- **router-dev-023 „Chci vyrobit skříň.“** (`unclear`): `naive_cs` → `unsupported` (0,85). Příklad přímo z UC-05; jednoduchá Choice nerozliší „mimo rozsah“ a „zatím nevím, co spočítat“. `v2` správně (`other_request`, `concrete` nízké).
- **router-dev-009 „Dělám regál: 4 nohy 1,8 m a 12 příček 80 cm…“** (`cutting_1d`): všechny rozložené varianty → `unclear`, Noul `concrete` 0,27–0,42, přestože díly i délky zpráva uvádí. Zmínka o výrobku (regál) stahuje Noul dolů; `task` = `cutting_bars` 0,98.
- **router-dev-013 „Udělej mi kalkulaci, sazba 500 Kč/h, práce 3 hodiny, přirážka 15 %.“** — záměr: všechny varianty `result_question` (~0,8) místo `change_order`. Diskutabilní štítek: uživatel zadává vstupy kalkulace (nová revize), ale formuluje to jako žádost o výsledek. Pro M3 rozhodnout, zda zadání vstupů kalkulace je `change_order`, nebo to řeší kód (přítomnost čísel).
- `decomposed_cs` / `_en` (1. iterace) navíc posílaly do `unclear` i jasné nepodporované úlohy (faktura, počasí, bedny) a „nacenit zakázku“, protože Noul „je jasné, co **spočítat**“ je u nich nízký — chyba pravdivostní tabulky, ne Jev; opraveno ve `v2`.

### Další pozorování

- **Pořadí možností:** obrácené pořadí v Choice (`decomposed_cs_reversed`) dalo stejná rozhodnutí kromě jednoho posunu v pásmu kalibrace; vliv pořadí (známá slabina Jev) se na této sadě neprojevil.
- **Opakovatelnost:** `decomposed_cs` a `_reversed` mají pro stejné vstupy pravděpodobnosti lišící se v setinách.
- **Konzistence otázek:** otázky v jednom požadavku se nevidí navzájem, takže `task` a `intent` mohou být v rozporu (např. `result_question` bez spočítaného plánu); kontrola konzistence patří do kódu (spec kap. 6).

## Doporučení

1. **Výchozí implementace pro M3: `JevRouter`.** Čeština funguje, latence ~150 ms je pro interaktivní UI zanedbatelná a cena téměř nulová.
2. **Do M3 vzít obě nejlepší varianty** (`naive_cs` a rozložené otázky s pravdivostní tabulkou) a rozhodnout mezi nimi až na `router/test`. Rozložená varianta je čitelnější (rozhodnutí v kódu, samostatné rozlišení `unclear` × `unsupported`) a lépe rozšiřitelná o `cutting_2d`; jednoduchá je levnější o ~25 % tokenů.
3. **Prahy (výchozí, k ověření na test sadě):** pravděpodobnost zvolené možnosti < 0,9 → doptat se (nabídnout výběr nástroje); Noul `concrete` 0,3 / 0,7 podle tabulky. `confidence` nepoužívat jako bránu.
4. **Fallback:** při chybě API (síť, `429`, `5xx`) nic nepředstírat a nabídnout `ManualRouter` (výběr nástroje) a opakování; `LlmRouter` jako srovnávací varianta a druhá záloha, pokud je dostupný Groq. Chyba volání se nikdy nesmí vykládat jako `unclear`.
5. **Layo:** dokud TypeSafe nezveřejní lokální model, nepočítat s ním. Specifikace (UC-07, kap. 6 tabulka implementací, kap. 12 offline demo) s Layo počítá jako s offline routerem — její úprava je rozhodnutí autora (viz ADR-0004, otevřená otázka v `AGENTS.md`). Offline demo jde zajistit připravenými odpověďmi (UC-11) a ručním výběrem.
6. **Otázky Jev patří do správy promptů:** v M3 je uložit do Langfuse (nebo verzovaného modulu s exportem do `prompts/`), aby report mohl uvést jejich verzi.
