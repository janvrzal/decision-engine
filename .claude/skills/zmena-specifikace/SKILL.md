---
name: zmena-specifikace
description: Postup pro úpravu docs/specifikace.md DecisionEngine — verzování, záznam změn a kontrola konzistence napříč kapitolami. Použij, kdykoli se mění chování, rozsah, kritéria přijetí nebo když kód a specifikace přestanou odpovídat.
---

# Změna specifikace

Specifikace je zdroj pravdy o chování. Změny musí být dohledatelné a vnitřně konzistentní.

## 1. Rozhodni, kdo rozhoduje

- Změnu rozsahu, kritérií přijetí nebo chování vůči uživateli **schvaluje uživatel**. Předlož návrh s důvodem; neupravuj sám.
- Opravu překlepu, odkazu nebo zjevného rozporu, kde je správná varianta jednoznačná, můžeš udělat rovnou a uvést ji v PR.

## 2. Uprav

- Zvyš verzi v hlavičce (`0.2` → `0.3`; drobná oprava → `0.2.1`) a datum.
- Pod hlavičku do odstavce **Změny oproti …** stručně shrň, co se mění (nahraď předchozí shrnutí; historie je v gitu).
- Použij stejné termíny jako zbytek dokumentu (schopnost, zakázka, revize, výsledek, nejlepší nalezený …) a stejné identifikátory jako kód.

## 3. Projdi dotčená místa

Jedna změna obvykle zasahuje více kapitol. Zkontroluj vždy:

| Mění se… | Zkontroluj kapitoly |
|---|---|
| rozsah / funkce | 3, 4 (UI), 5 (UC), 9 (kritéria), 11 (pořadí), 12 (obhajoba), 13 |
| datový objekt | 7 (tabulka objektů), dotčené UC, formát exportu (UC-06) |
| solver / štítky | 5 (UC), 7, 8, 9 |
| AI / router | 6, 7, 9, 10, 14 a ADR-0004 |

Hledej starou formulaci v celém souboru (`grep`), ne jen v kapitole, kterou upravuješ.

## 4. Navaž

- Architektonické důsledky → nový ADR (skill `adr`).
- Pokud kód přestává odpovídat, zapiš to do PR jako známý rozdíl nebo ho oprav ve stejném PR.
- Commit: `docs(spec): …`.
