# Evaluace AI

Postup je ve skillu `.claude/skills/ai-evaluace/`. Kritéria přijetí jsou ve specifikaci, kap. 9.

## Sady

| Sada | `dev/` (ladění) | `test/` (jen měření) | Formát |
|---|---|---|---|
| Extrakce | 18 případů | 32 případů | jeden případ na soubor: `input`, `expected` (díly, sklad, prořez, ořez, zbytek, cíl), `tags` |
| Router | 31 případů | 52 případů | `cases.json`: `input.message`, `input.order`, `expected.capability`, `expected.intent` |
| Dialog | 3 scénáře | 10 scénářů, 39 kol | `turns`: `input`, `expected.outcome`, `expected.project` (stav zakázky po kole) |

Testovací sady napsal nezávislý agent, který prompty neladí, ještě před změnami promptů a routeru (commit `eval(sets)`). Při ladění promptů, popisů schopností nebo prahů se jejich obsah **nečte**. Kdyby se sada změnila, je nutné znovu změřit všechny varianty.

Otisky zamrazených test sad (SHA-256 spojených souborů seřazených podle názvu, prvních 16 znaků):

| Sada | Otisk |
|---|---|
| `extraction/test` | `ad1b2bd4894e77c5` |
| `router/test` | `acadfb4bc513c6a3` |
| `dialog/test` | `425fe7a1fdb1b844` |

Kontrola otisku:

```bash
cat $(ls evals/extraction/test/*.json | sort) | shasum -a 256 | cut -c1-16
```

## Spuštění (placená API, jen na pokyn autora)

```bash
uv run --env-file .env python scripts/eval_extraction.py --set dev
uv run --env-file .env python scripts/eval_router.py --set dev --routers jev,llm
uv run --env-file .env python scripts/eval_dialog.py --set dev
```

Měření na test sadě je stejné s `--set test`. Surová data jdou do `reports/raw/` a report se dá přepočítat bez volání API přes `--from-raw <soubor>`.

## Co report uvádí

- Přesnost s 95% Wilsonovým intervalem: u desítek případů samotné procento neodliší 80 % od 90 %.
- Párové srovnání modelů na stejných případech (přesný McNemarův test) místo porovnání dvou procent.
- **Vymyšlená hodnota**: model vrátil údaj, který zadání neuvádí (očekávané `null` nebo prázdný sklad).
- **Neoznačená chyba**: chybná hodnota, kterou aplikace uživateli neoznačila jako odhad AI (pravidlo 8; ukotvení čísel v `core/number_anchors.py`).
- U routeru matici záměn a latenci, u dialogu správná kola a celé scénáře bez chyby.
- Model, verzi promptu a schéma; Groq není deterministický ani při `temperature=0`, proto se u rozhodujících srovnání běh opakuje (aspoň 3×) a uvádí rozptyl.

Varianta, model nebo práh vybraný na dev sadě se na dev sadě hlásí jako optimistický odhad; platný je až výsledek na test sadě.
