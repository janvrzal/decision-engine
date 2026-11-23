---
name: ui-frontend
description: Konvence a postup pro práci na frontendu DecisionEngine (SvelteKit, Svelte 5, TypeScript, Tailwind, Bits UI, design systém v docs/design-system) — vzhled, stavy panelů, formátování, přístupnost, napojení na API a ověření v běžící aplikaci. Použij při jakékoli změně UI, komponenty, stylu nebo uživatelského toku.
---

# Práce na frontendu

UI je jediný povinný a hodnocený požadavek zadání. Cílem je, aby aplikace působila jako hotový produkt, ne jako demo.

## Hranice odpovědnosti

- Frontend **zobrazuje view model** z backendu a **posílá události** (`POST /api/sessions/{id}/events`). Nepočítá metriky, ceny, kapacity ani přechody stavu (ADR-0006, ADR-0007).
- Jediná „logika“ ve frontendu: formátování (`Intl.NumberFormat('cs-CZ')`, jednotky), lokální stav formulářů před odesláním a čistě vizuální interakce (zvýraznění dílu v plánu).
- Typy API se generují (`pnpm generate:api`); ruční typy odpovědí API jsou zakázané. Po změně API v backendu typy přegeneruj ve stejném PR.

## Konvence kódu

- Svelte 5 s runes (`$state`, `$derived`, `$props`), TypeScript strict, žádné `any`.
- Komponenty v `frontend/src/lib/components/`, stránky v `frontend/src/routes/`. Jedna komponenta = jeden soubor, ideálně do ~200 řádků.
- Vzhled určuje design systém v `docs/design-system/`: principy a odkazy v `README.md`, tokeny v `tokens.css`, komponenty v `komponenty.md`, plán řezání v `plan-rezani.md`, texty a formáty v `obsah.md`. Živé ukázky jsou v Claude Design (odkaz v README); při rozporu platí repozitář.
- Komponenty jen z inventáře v `komponenty.md`. Obecné prvky obalují Bits UI s vlastním vzhledem (`src/lib/components/ui/`), shadcn-svelte se nepoužívá (ADR-0010). Doménové chování (tabulka dílů, zvýraznění v plánu, posouvání dialogu) je v `src/lib/behaviors/*.svelte.ts` s testy ve Vitestu.
- Styly přes Tailwind a tokeny z `docs/design-system/tokens.css` importované v `src/app.css`; výchozí paleta Tailwindu je vypnutá. **Žádné pevné barvy, velikosti ani rozestupy mimo tokeny**, žádné inline `style` kromě dynamických hodnot (např. souřadnice v plánu).
- Texty česky, krátké, v jazyce dílny („Řezání tyčí“, ne „cutting_1d“), podle tónu, vzorů a glosáře v `docs/design-system/obsah.md`. Interní pojmy (revize, router, tokeny) jen ve vývojářském panelu.

## Stavy — každý panel je má všechny

| Stav | Co uživatel vidí |
|---|---|
| prázdný | co sem patří a jedna jasná akce (např. příklad zadání) |
| načítání | průběh u konkrétního panelu, ne blokace celé stránky; u AI a solveru možnost zrušit |
| chyba | co se stalo lidsky, co s tím (opakovat, ručně, upravit pole); konkrétní pole zvýrazněné |
| neaktuální | výsledek viditelně označený, export plánu nedostupný, výrazná akce „Přepočítat“ |
| hotovo | výsledek se štítkem stavu plánu (Optimální / Nejlepší nalezený / Částečný / Bez řešení) |

## Formát čísel a jednotek

Úplná pravidla jsou v `docs/design-system/obsah.md`; nejčastější:

- Délky: `1 250 mm`; od 10 m volitelně i metry v podtextu (`12,5 m`).
- Peníze: `1 234,50 Kč`; chybějící cena je „chybí cena“, nikdy `0 Kč`.
- Procenta: `87,4 %` (s mezerou).
- Hodnoty nepotvrzené nebo doplněné modelem mají viditelné označení (přerušovaný okraj `proposal` a ikona „?“) a původ v tooltipu.

## Přístupnost a rozložení

- Vše ovladatelné klávesnicí včetně editace tabulek; viditelný fokus; logické pořadí tabulátoru.
- Kontrast WCAG AA; informace nikdy jen barvou (stav má i ikonu nebo text).
- Plán v SVG má `title`/`aria-label` a textový rozpis jako alternativu.
- Od 1280 px: dialog vlevo, pracovní plocha vpravo. 768–1279 px: dialog jako vysouvací panel zleva (`Sheet`), pracovní plocha přes celou šířku. Ověř 1440 i 768 px.

## Postup u změny UI

1. Ujasni, který krok hlavního toku a které stavy se mění (kap. 4 a 5 specifikace).
2. Pokud se mění view model nebo události, nejdřív backend (reducer + testy v `tests/flow/`), pak `pnpm generate:api`.
3. Implementuj komponentu se všemi stavy z tabulky výše.
4. Spusť aplikaci (`uv run decision-engine` + `pnpm dev`) a **projdi změnu v prohlížeči** na šířce 1440 px i 768 px; v PR ověření popiš (screenshoty se nepřikládají).
5. `pnpm check && pnpm lint && pnpm test`; u změny hlavního toku i `pnpm test:e2e`.

## Checklist před PR

- [ ] Všechny stavy panelu existují a jsou vidět v běžící aplikaci.
- [ ] Jen tokeny a komponenty z design systému, žádné jednorázové styly; nová komponenta nebo varianta je doplněná v `docs/design-system/komponenty.md`.
- [ ] Čísla a jednotky ve formátu `cs-CZ`, žádné interní pojmy v hlavním UI.
- [ ] Klávesnice a fokus fungují; axe bez závažných nálezů.
- [ ] Rozložení ověřené na 1440 px a 768 px a popsané v PR.
- [ ] Frontend nic nepočítá; typy API vygenerované.
