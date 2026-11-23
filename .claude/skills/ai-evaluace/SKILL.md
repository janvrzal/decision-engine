---
name: ai-evaluace
description: Postup pro tvorbu evaluačních sad a měření AI částí DecisionEngine (router Jev/Layo/LLM, extrakce, dialog) včetně pravidla oddělených dev/test sad a formátu reportu. Použij při ladění promptů, přidávání případů, spouštění evaluace nebo psaní výsledků do reportu.
---

# AI evaluace

## Struktura

```
evals/
  router/      dev/  test/   # zpráva + stav zakázky → očekávaná schopnost a záměr
  extraction/  dev/  test/   # zadání → očekávaná strukturovaná data (kritická pole)
  dialog/      dev/  test/   # vícekolové scénáře → očekávaný stav zakázky po každém kole
  reports/                   # vygenerované reporty (commitují se)
```

Případy jsou JSON soubory s polem `id`, `input`, `expected`, `tags` (např. `unclear`, `jednotky_cm`, `slang`) a `author_note`.

## Pravidlo oddělených sad (nejdůležitější)

- **Ladění** promptů, popisů schopností, prahů confidence a few-shot příkladů jen nad `dev/`.
- **Měření** do reportu jen nad `test/`.
- Při ladění **nečti obsah `test/`**, nekopíruj z něj příklady a neupravuj ho, aby výsledek vyšel lépe.
- Pokud se `test/` po měření změní (oprava chybného `expected`), zapiš to do reportu a přeměř všechny varianty.
- Nové případy pro `test/` vznikají před laděním, ideálně je píše člověk.

## Kritéria (spec kap. 9)

| Sada | Min. velikost | Cíl |
|---|---|---|
| router/test | 50 | ≥ 90 % správných voleb vč. `unclear`, `unsupported` |
| extraction/test | 30 (1D) | ≥ 90 % úplné shody kritických polí: rozměry, počty, jednotky, vstupní formáty |
| dialog/test | 10 scénářů × ≥ 3 kola | žádná ztráta dat, správné doptání u nejasného odkazu |

Rozložení kategorií má odpovídat realitě, ne být uměle vyvážené; uveď ho v reportu.

## Spuštění

- Evaluace volá placená API → spouští se jen na pokyn uživatele.
- Router: stejná sada na všech dostupných implementacích (Jev, Layo, LLM).
- Odpovědi se cachují podle (vstup, model, verze promptu/schématu), aby opakované spuštění nestálo peníze; přeměření po změně promptu musí cache obejít.

## Report (`evals/reports/RRRR-MM-DD-<sada>.md`)

Musí obsahovat:

- datum, model a přesnou verzi (např. `jev-1.14.0`), implementaci routeru, verzi promptu/schématu,
- velikost sady a rozložení kategorií,
- celkovou přesnost a matici záměn / chyby podle kategorií,
- u routeru kalibraci: přesnost v pásmech confidence a zvolený práh doptání,
- latenci (medián, p95) a cenu,
- seznam chybných případů s krátkou analýzou,
- formulaci, že metriky platí pro tuto sadu a podmínky, nejsou obecnou zárukou přesnosti.
