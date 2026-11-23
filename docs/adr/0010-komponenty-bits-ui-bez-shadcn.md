# ADR-0010: Komponenty nad Bits UI s vlastním vzhledem, bez shadcn-svelte

**Stav:** přijato  
**Datum:** 2026-11-23  
**Souvisí se:** ADR-0007 (část „Vzhled“ nahrazuje), specifikace kap. 4 a 9, `docs/design-system/`

## Kontext

ADR-0007 zvolilo pro vzhled Tailwind CSS s komponentami shadcn-svelte, které stojí na Bits UI. Hodnotí se jen kvalita a použitelnost UI a výsledek má působit jako hotový produkt s vlastní identitou. Vzhled shadcn je dnes velmi rozšířený a aplikace postavená na jeho výchozích stylech by vypadala jako mnoho jiných. Design systém DecisionEngine proto definuje vlastní tokeny a vizuální jazyk.

Chování přístupných komponent (klávesnice, fokus, ARIA, past fokusu v dialogu, pozicování menu) je pracné a rizikové. Kritérium „UI – přístupnost“ v kap. 9 vyžaduje ovládání klávesnicí a axe bez závažných nálezů, takže chování nechceme psát sami.

## Rozhodnutí

- **Chování obecných prvků** (dialog, menu, select, combobox, tooltip, popover, záložky, přepínač, zaškrtávátko) poskytuje knihovna **Bits UI** (headless, Svelte 5).
- **Vzhled je vlastní.** Komponenty v `frontend/src/lib/components/ui/` obalují Bits UI a stylují se Tailwindem jen přes tokeny design systému (`docs/design-system/`). Nepoužíváme CLI ani styly shadcn-svelte a jeho názvy CSS proměnných (`--primary`, `--ring`…) nejsou závazné.
- **Doménové chování**, které žádná knihovna nemá (pohyb v editovatelné tabulce dílů, propojení zvýraznění tabulky a plánu, posouvání dialogu, potvrzení nepotvrzené hodnoty), je ve vlastní vrstvě `frontend/src/lib/behaviors/*.svelte.ts`: funkce a třídy s runes, bez markupu a stylů, testované Vitestem.
- Prvky, které Bits UI nemá a nepotřebují složité chování (tlačítko, vstupní pole, štítek, karta, tabulka), jsou nativní HTML elementy s našimi styly.

## Zvažované varianty

- **shadcn-svelte (dosavadní volba)** — rychlý start a hotové styly, ale vzhled, který je dnes všude; přestylování po komponentách by stálo podobně jako vlastní vzhled a nechávalo by stopy výchozího stylu. Zamítnuto.
- **Ark UI / Zag.js** — čisté oddělení chování jako stavové automaty, více komponent (např. Number Input); chování komponent v ukázkách působilo nepřirozeně a Svelte je u knihovny až čtvrtý framework. Zamítnuto.
- **Melt UI (`melt`, nová generace)** — buildery s maximální kontrolou nad markupem a nativními runes; verze 0.x a málo komponent. Zamítnuto.
- **Vlastní vrstva chování pro všechno** — žádná závislost, ale největší práce a riziko u přístupnosti. Zamítnuto; vlastní vrstvu používáme jen pro doménové chování.

## Důsledky

- Plná kontrola nad vzhledem a přístupnost obecných prvků z odladěné knihovny. Za to každou komponentu stylujeme sami podle inventáře v `docs/design-system/`.
- Mechanicky hlídané: axe v Playwright testech hlavního toku; Vitest pro `behaviors/`; lint pravidlo nebo kontrola v review proti pevným barvám mimo tokeny (skill `ui-frontend`).
- Na disciplíně: nové komponenty jen podle inventáře design systému, žádné importy stylů třetích stran.
- Přehodnotit, pokud Bits UI přestane držet krok se Svelte 5 nebo pokud by chybějící komponenta vyžadovala víc než malou vlastní vrstvu chování.
