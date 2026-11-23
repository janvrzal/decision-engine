# Extrakce 1D: porovnání modelů na Groqu (dev sada)

Spike #6 (M0), podklad pro ADR-0008. **Jde o ladicí sadu `evals/extraction/dev/`, ne o měření na `test/`.** Metriky platí jen pro tuto malou sadu a uvedené podmínky, nejsou obecnou zárukou přesnosti. Měření pro specifikaci (kap. 9) proběhne na `extraction/test` v M8.

## Podmínky

| | |
|---|---|
| Datum | 23. 11. 2026 |
| Poskytovatel | Groq, OpenAI-kompatibilní API, free tier (`on_demand`) |
| Modely | `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` (id modelu Groq, jemnější verzi API neuvádí) |
| Prompt | `extract-proposal-1d` v1 z Langfuse (štítek `production`), opravný `repair-invalid-json` |
| Schéma | `ExtractionOutput`, otisk `d06dc2c69ac3` |
| Cesta | stejná jako v aplikaci: `handle` → `run_extraction` → `OpenAICompatibleLlm`, `temperature=0`, nejvýš 1 opravný pokus, SDK opakuje dočasné chyby 2× |
| Formát výstupu | hlavní běh `response_format: json_object` (jako v adaptéru); sonda `json_schema` (`strict: false`) na prvních 5 případech |
| Trasování | Langfuse zapnuté, session `eval-extraction-<běh>-<model>` |
| Skript | `scripts/eval_extraction.py`, surové výsledky v `evals/reports/raw/` |
| Běhy | `20261123-2046-100b` (celá sada, 3 modely); `…-2057-dd7c`, `…-2057-20f6`, `…-2058-386c` (dopočet 4 případů, které v hlavním běhu narazily na limit 429); `…-2058-ec4b` (sonda `json_schema`) |

Report z běhů lze bez volání modelu znovu vypsat:

```bash
uv run python scripts/eval_extraction.py --from-raw evals/reports/raw/*json_object-20261123-2046-100b.json evals/reports/raw/*json_object-20261123-205[78]*.json
```

## Sada

18 ručně označených českých zadání (`extraction-dev-01` až `-18`). Kritická pole: díly (délka a počet), skladové délky, ceny za tyč, prořez, ořez, minimální zbytek. Cíl optimalizace se hodnotí zvlášť. Díly a sklad se porovnávají bez ohledu na pořadí.

Rozložení štítků (případ může mít víc): `jednotky_m` 6, `chybi_prorez` 4, `jednotky_cm` 3, `jednotky_mm` 3, `desetinna_carka` 3, `chybi_sklad` 3, `chybi_cena` 3, `cil` 3, `oddelovac_tisicu` 2, `slovni_cisla` 2, `neprima_formulace` 2, `vice_skladovych` 2, `zkracene` 2, `nejasne` 2 a po jednom `parametry`, `hovorove`, `cena_za_metr`, `kontextove_cislo`, `desetinna_cena`, `pocet_tyci_v_textu`, `cena_format`, `bez_udaju`, `uplne`, `smisene_jednotky`, `chybi_pocet`. Rozložení odpovídá představě autora o běžných zadáních, ne skutečným datům.

## Výsledky: `json_object` (hlavní běh + dopočet)

| Model | Úplná shoda kritických polí | Platné bez opravy | Platné celkem | Cíl správně | Čas modelu (Groq) | Výstupní tokeny / případ (z toho reasoning) | Cena za 18 případů | Cena / extrakce |
|---|---|---|---|---|---|---|---|---|
| `openai/gpt-oss-120b` | **15/18 (83 %)** | 18/18 | 18/18 | 18/18 | ~1,5 s | 621 (450) | 0,0109 USD | ~0,0006 USD |
| `openai/gpt-oss-20b` | **14/18 (78 %)** | 18/18 | 18/18 | 17/18 | ~0,6–0,9 s | 831 (587) | 0,0066 USD | ~0,0004 USD |
| `qwen/qwen3.8-27b` | **17/18 (94 %)** | 18/18 | 18/18 | 18/18 | ~0,6–0,7 s | 254 (0) | 0,0397 USD | ~0,0022 USD |

Cena podle ceníku Groq z ADR-0009 (vstup / výstup USD za 1M tokenů: 0,15/0,60; 0,075/0,30; 0,80/4,00), reasoning tokeny jako výstup, cache Groq nezapočtena. Vstup je u všech ~1 550 tokenů na volání (prompt obsahuje JSON schéma).

**Latence.** Hlavní běh posílal případy hned po sobě a free tier Groq má limity 8 000 tokenů/min (gpt-oss) a 1 000 výstupních tokenů/min (qwen). SDK proto často čekalo na `retry-after`; naměřené časy běhu (medián 6–12 s, p95 17–21 s) jsou čekání na limit, ne rychlost modelu, a 4 případy skončily chybou 429 (dopočítány znovu s pauzou). Sloupec *Čas modelu* je `usage.total_time` z Groq z volání s pauzou 20 s (dopočet a sonda `json_schema`, 4–7 volání na model); celkový čas volání s pauzou byl 0,4–4,8 s. Pro jednoho uživatele aplikace je to v pořádku, pro evaluaci je potřeba pauza (`--pause 20`).

Chyby podle kategorií (počet případů):

| Kategorie | `gpt-oss-120b` | `gpt-oss-20b` | `qwen3.8-27b` |
|---|---|---|---|
| `parts_pocet_polozek` (chybějící nebo přebytečný díl) | 1 | 3 | 1 |
| `parts_delka` | 1 | 0 | 0 |
| `stock_length` | 1 | 2 | 0 |
| ceny, prořez, ořez, min. zbytek | 0 | 0 | 0 |

### Chybné případy

- **`extraction-dev-09`, všechny tři modely** — „Hliníkový profil: 14× 37,5 cm. Mám tyče 4 m za 389,50 Kč…“: žádný díl, sklad a cena správně. Zápis „14× 37,5 cm“ hned za popisem profilu modely berou jako rozměr profilu. Kandidát na úpravu promptu (příklad zápisu `N× délka`), ladit jen na dev sadě.
- **`extraction-dev-14`, oba gpt-oss** — „Mám doma 2 tyče 6 m…“: dvě stejné skladové položky 6 000 mm místo jedné. Schéma nemá počet kusů na skladě, modely ho vyjádří duplikací. Qwen vrátil jednu položku. Kandidát na pravidlo v promptu (a otázka pro specifikaci, zda evidovat dostupný počet tyčí).
- **`extraction-dev-04`, `gpt-oss-120b`** — „dvanáct sloupků po metru dvacet a tři madla po 2,4 metru“: sloupky 1 000 mm místo 1 200 a madla **23 ks** místo 3. Nejzávažnější chyba běhu: vymyšlené číslo, které by uživatel musel v návrhu odhalit sám.
- **`extraction-dev-02`, `gpt-oss-20b`** — přidal třetí díl „trubka 25×25“ bez délky s počtem 1 (popis materiálu jako díl).
- **`extraction-dev-16`, `gpt-oss-20b`** — degenerovaný výstup: správný díl 1 200 mm × 25 a za ním 75 prázdných dílů (všechna pole `null`), sklad chybí. Schéma prošlo, takže to oprava nezachytila; v návrhu by se objevily prázdné řádky.

Případy s chybějícími údaji (`extraction-dev-07` bez počtu, `-17` bez údajů, cena za metr v `-05`) zvládly všechny modely: nic si nevymyslely.

## Sonda: `json_schema` vs. `json_object`

Prvních 5 případů, `response_format: {"type": "json_schema", "strict": false}` se schématem `ExtractionOutput`:

| Model | Úplná shoda | Platné | Poznámka |
|---|---|---|---|
| `openai/gpt-oss-120b` | 4/5 | 5/5 | stejný výsledek jako `json_object` (chyba v `-04` se opakuje) |
| `openai/gpt-oss-20b` | 3/5 | 5/5 | nově duplikovaný díl v `-05` |
| `qwen/qwen3.8-27b` | 0/5 | 3/5 | 2× chyba 400 „Failed to generate JSON“, 3× prázdný výstup (žádné díly ani sklad) |

`json_schema` nic nezlepšil, u qwen výstup rozbil a vstup prodražil (schéma jde v promptu i v `response_format`, ~2 400 místo ~1 550 tokenů). Tool calling jsem netestoval: `json_object` s validací Pydanticem dal 18/18 platných odpovědí bez opravy u všech modelů, takže není co zlepšovat a přidávat druhou cestu do adaptéru nemá oporu v datech.

## Doporučení

**Výchozí model: `qwen/qwen3.8-27b` s `response_format: json_object`** (beze změny adaptéru).

- Nejvyšší shoda kritických polí (17/18); jediná chyba je případ, na kterém selhaly všechny modely.
- Žádný vymyšlený údaj ani nadbytečná položka; gpt-oss-120b v `-04` vymyslel počet kusů, gpt-oss-20b produkuje nadbytečné a prázdné díly.
- Krátký výstup bez reasoning tokenů (~250 tokenů) a nejkratší čas modelu; to vyvažuje přísnější výstupní limit free tieru (1 000 tokenů/min ≈ 4 extrakce za minutu, srovnatelné s gpt-oss při 8 000 TPM).
- Cena ~0,002 USD za extrakci je vyšší (≈ 4× gpt-oss-120b), ale pro semestrální aplikaci zanedbatelná.

**Záloha: `openai/gpt-oss-120b`** — druhý nejlepší, levnější a jako jediný z gpt-oss bez degenerovaných výstupů; podporuje i `json_schema`. `openai/gpt-oss-20b` nedoporučuji.

Výhrady: 18 případů je málo, rozdíl qwen a gpt-oss-120b jsou 2 případy a není statisticky průkazný. Volba se potvrdí měřením na `extraction/test` v M8; pokud tam qwen nebude nejlepší, změna je jen hodnota `LLM_MODEL`.

## Další kroky (mimo tento spike)

- Prompt: zápis „N× délka“ za popisem profilu (`-09`) a počet tyčí na skladě (`-14`); ladit na dev sadě, nová verze se štítkem `staging`.
- Adaptér: odmítnutí Groq `json_validate_failed` (400) se dnes vrací jako `Err` bez opravného pokusu; zvážit jeden opravný pokus i pro tento případ.
- Validace návrhu: ověřit, že prázdné díly (všechna pole `null`) a duplicitní skladové délky se v návrhu ukážou jako chyba a neprojdou tiše.
