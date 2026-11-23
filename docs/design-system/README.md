# Design systém DecisionEngine

DecisionEngine pomáhá malé dílně dostat se od českého zadání k nářezovému plánu a ceně zakázky. Rozhraní má působit jako přesný pracovní nástroj: klidná plocha, čísla v popředí, jeden jantarový akcent a jemné linky jako na technickém výkrese. Hodnotí se hlavně čistota a použitelnost UI (`docs/zadani.md`), proto se každá obrazovka skládá jen z tokenů a komponent tohoto systému.

Tento adresář je zdroj pravdy. Živé ukázky barev, typografie a komponent jsou v Claude Design ([DecisionEngine](https://claude.ai/artifact/9nrimF6apkqDpmY61Tmz2V)); při rozporu platí repozitář.

| Dokument | Obsah |
|---|---|
| [`foundations.md`](foundations.md) | barvy, typografie, rozestupy, zaoblení, stíny, pohyb; ověření kontrastu |
| [`tokens.css`](tokens.css) | tokeny pro Tailwind CSS v4 (`@theme`), import do `frontend/src/app.css` |
| [`komponenty.md`](komponenty.md) | inventář komponent: chování, varianty, stavy a pravidla |
| [`plan-rezani.md`](plan-rezani.md) | vizuální jazyk plánu řezání pro UI i PDF |
| [`obsah.md`](obsah.md) | tón textů, vzory hlášek, formát čísel a jednotek `cs-CZ`, glosář |

Související rozhodnutí: [ADR-0007](../adr/0007-webove-ui.md) (SvelteKit, Tailwind), [ADR-0010](../adr/0010-komponenty-bits-ui-bez-shadcn.md) (Bits UI s vlastním vzhledem). Obrazovky a toky popisuje `docs/service-design/`.

## Principy

1. **Vždy je jasný další krok.** Uživatel vidí, ve kterém kroku je (Zadání → Kontrola údajů → Plán a cena) a co má udělat dál. V panelu je nejvýš jedna akce ve výplni `primary`; ostatní akce jsou obrysové nebo textové. *(spec. kap. 4: jeden hlavní tok)*
2. **Čísla jsou hlavní obsah.** Rozměry, počty a ceny mají tabulární číslice, v tabulkách jsou zarovnané vpravo a mají vždy jednotku ve formátu `cs-CZ` (`1 250 mm`, `1 234,50 Kč`, `87,4 %`). Typografie a rozestupy slouží čitelnosti tabulek a plánu, ne dekoraci. *(kap. 4: čísla a jednotky)*
3. **Výsledek poctivě ukazuje svůj stav.** U každého výsledku je vidět, nakolik mu lze věřit: optimální, nejlepší nalezený, částečný nebo bez řešení. Dále je vidět, jestli je neaktuální a které hodnoty nikdo nepotvrdil. Stav se nikdy nesděluje jen barvou, vždy má i text a ikonu. Každý panel má navržené stavy prázdný, načítání, chyba, neaktuální a hotovo. *(kap. 4: stavy; AGENTS.md pravidlo 9)*
4. **Data jsou důležitější než konverzace.** AI navrhuje, uživatel potvrzuje. Rozměry, počty a ceny jsou v editovatelných tabulkách, ne jen ve zprávách. Co ještě neplatí (návrh změny, odhad modelu, výchozí hodnota), je odlišené barvou `proposal` a přerušovanou čarou. *(kap. 4: dialog a kontrola údajů; AGENTS.md pravidla 7 a 8)*
5. **Klidná plocha s přesnou kresbou.** Teplé neutrální barvy, jeden jantarový akcent, vlasové linky místo stínů. Všechno vychází z tokenů a jedné sady komponent, žádné jednorázové styly. *(kap. 4: jednotný vzhled; kap. 9: UI – vzhled)*
