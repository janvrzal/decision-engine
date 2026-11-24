# Komponenty

Inventář vychází z low-fi prototypu ve FigJamu (41 rámců A1–G3, viz `docs/service-design/04-mapa-obrazovek.md`) a z kap. 4 a 5 specifikace. Obrazovky a panely (`ProjectScreen`, `ChatPanel`, `PlanPanel` …) nejsou komponenty, skládají se z komponent níže.

Pravidla pro všechny komponenty:

- Chování obecných prvků dodává Bits UI, vzhled je vlastní a jen z tokenů ([ADR-0010](../adr/0010-komponenty-bits-ui-bez-shadcn.md)). Doménové chování je ve `frontend/src/lib/behaviors/`.
- Ovládací prvky mají výšku 32 px (`h-8`), štítky 22 px, čipy 24 px. Fokus je vždy viditelný (`focus-ring`).
- Stav nikdy jen barvou: vždy text, ikona nebo vzor.
- Ikony: [Lucide](https://lucide.dev) (`@lucide/svelte`, licence ISC), 16 px, tah 1,5 px, barva podle textu vedle. Emoji se v UI nepoužívají.
- Komponenta nic nepočítá; dostává hotové hodnoty z view modelu a jen je formátuje (`cs-CZ`).

## Základní prvky

| Komponenta | Chování | Varianty a stavy | Pravidla |
|---|---|---|---|
| `Button` | nativní `<button>` | `primary`, `secondary`, `ghost`, `danger`; výchozí, hover, fokus, stisk, neaktivní, načítání | V panelu nejvýš jeden `primary`. Neaktivní tlačítko má v tooltipu nebo pod sebou důvod („Nejdřív opravte 2 pole“). Neaktivní tlačítko má `aria-disabled` místo `disabled`, aby zůstalo v pořadí tabulátoru a důvod šel přečíst i z klávesnice. Načítání: po spodní hraně zametá linka 2 px v barvě textu (1,2 s), text i šířka zůstávají, `aria-busy`; při omezeném pohybu linka zmizí. |
| `IconButton` | nativní `<button>` | `ghost`, `secondary`; velikost 32 a 24 px | Vždy `aria-label` a tooltip s názvem akce. |
| `Chip` | nativní `<button>` | výchozí, vybraný | Ukázky zadání, rychlé úpravy a volby doptání v dialogu. Nikdy nenahrazuje hlavní akci. |
| `Badge` | — | `neutral`, `info`, `success`, `warning`, `danger`, `proposal` | Krátký štítek (nový, sklad, nákup, Demo, Příklad, „neuloženo“ v hlavičce zakázky jako `warning`). Styl `label`, výška 22 px, vždy text, volitelně ikona. |
| `Kbd` | — | — | Klávesová zkratka v nápovědě („Esc“). |
| `Icon` | — | 16 px | Ikony Lucide, viz výše. |
| `Loader` | — | malý 44 × 12 px, velký 96 × 16 px | Indikátor práce místo spinneru: do malé tyče postupně padají díly v barvách plánu oddělené prořezem (cyklus 1,8 s). Vždy s textem; v tlačítku se nepoužívá. Text fáze AI má jemný přeliv. Při omezeném pohybu stojí se dvěma vloženými díly. |
| `Tooltip` | Bits Tooltip | — | Vysvětlení nepotvrzené hodnoty, neaktivní akce, ikon. Otevře se i fokusem z klávesnice. Nenese jedinou kopii důležité informace. |
| `DropdownMenu` | Bits DropdownMenu | — | Akce „⋯“ v hlavičce zakázky (na střední šířce). Neaktivní položka má důvod stylem `small` pod názvem, protože v menu se tooltip nezobrazí. |
| `Collapsible` | Bits Collapsible | sbaleno, rozbaleno | „Další nastavení“, „Rozpis po tyčích“. Šipka se otáčí, popisek se nemění. |
| `Tabs` | Bits Tabs | — | Vývojářský panel, sklad. Aktivní záložka má podtržení `accent-text` 2 px. |

## Formuláře

| Komponenta | Chování | Varianty a stavy | Pravidla |
|---|---|---|---|
| `TextField`, `TextArea` | nativní | výchozí, fokus, neaktivní, jen ke čtení, chyba | Popisek nad polem (`Label`, Bits Label), nápověda a chyba pod polem stylem `small`. Chyba = okraj `danger`, ikona a text. |
| `NumberUnitInput` | nativní + `behaviors/number-input` | výchozí, nepotvrzená, změněná, chyba | Číslo vpravo s `numeric`, jednotka (mm, ks, Kč, %, s) uvnitř pole vpravo v `ink-muted`. Přijímá čárku i tečku, zobrazuje `cs-CZ` (`12 500`, `1 234,50`); formát se použije při potvrzení hodnoty, ne během psaní. |
| `RadioCardGroup` | Bits RadioGroup | výchozí, vybraná, neaktivní s důvodem, chyba skupiny | Cíl optimalizace: karta s názvem a jednou větou nápovědy; výchozí volba má poznámku „Výchozí“. |
| `Switch` | Bits Switch | zapnuto, vypnuto, neaktivní | Jen pro okamžitě platná nastavení („Použít sklad“). |
| `Checkbox` | Bits Checkbox | zaškrtnuto, nezaškrtnuto, neurčité | Výběr řádků (zápis do skladu). |
| `Select` | Bits Select | výchozí, otevřený, neaktivní | Krátké výběry (materiál, skladová délka). |
| `SegmentedControl` | Bits ToggleGroup | vybraná položka, neaktivní položka s důvodem | Jen vývojářský panel (implementace routeru). |
| `DropZone` | nativní `<input type=file>` + drag & drop | výchozí, přetahování, kontrola souboru, chyba | Načtení zakázky z JSON. Vždy i tlačítko „Vybrat soubor“. |

## Zpětná vazba a stav

| Komponenta | Chování | Varianty a stavy | Pravidla |
|---|---|---|---|
| `Alert` | `role="status"` / `role="alert"` | `info`, `warning`, `danger` | Ikona, krátký nadpis, jedna věta, nejvýš dvě akce. Chyba AI, chybějící ceny, chyba souboru. |
| `ProgressBar` | Bits Progress | určitý, neurčitý | Průběh výpočtu s časovým limitem („3,5 s z 10 s“) a akcí Zrušit vedle. |
| `EmptyState` | — | v panelu, celostránkový | Co sem patří (nadpis + jedna věta) a jedna akce. Celostránkový stav (backend nedostupný, relace vypršela) má navíc ikonu. |
| `SolutionStatusBadge` | — | optimální, nejlepší nalezený, částečný, bez řešení, neaktuální | Viz [Doménové komponenty](#doménové-komponenty). |

Toasty se nepoužívají: chyby a potvrzení zůstávají v panelu nebo v historii dialogu, kde je uživatel najde.

## Modální okna

| Komponenta | Chování | Varianty | Pravidla |
|---|---|---|---|
| `Modal` | Bits Dialog | šířka 520, 640, 720 px | Příklady, Načíst zakázku (`ImportDialog`: výběr souboru i přetažení, chyba načtení jako `Alert danger` v okně), Zápis do skladu. Nadpis, obsah, patička s akcemi vpravo (hlavní akce poslední). Zavření ✕, Esc a klik mimo. |
| `ConfirmDialog` | Bits AlertDialog | — | Zahození rozpracované zakázky nebo změn (`DiscardProjectDialog`: Zrušit · Zahodit zakázku / Zahodit a načíst · Uložit a pokračovat). Fokus na bezpečné akci („Zrušit“), destruktivní akce je `danger`. Klik mimo okno nezavře. |
| `Sheet` | Bits Dialog | vlevo (dialog na střední šířce, 380 px), vpravo (vývojářský panel, 460 px) | Vysouvací panel přes obsah se `shadow-overlay`. |

## Data

| Komponenta | Chování | Pravidla |
|---|---|---|
| `DataTable` | nativní `<table>` | Záhlaví stylem `label` na `surface-sunken`, řádky oddělené `border`, čísla vpravo s `numeric`. Rozpis po tyčích, sklad, zápis do skladu. |
| `KeyValueList` | nativní `<dl>` | Popisek `ink-muted` vlevo, hodnota vpravo. Vývojářský panel, souhrny. |
| `Timeline` | nativní `<ol>` | Záznamy volání AI a historie skladu; položka má čas, text a stav (ikona + slovo). |
| `Meter` | Bits Meter | Jen vývojářský panel (jistota routeru). |

## Doménové komponenty

### `StepIndicator`

Tři kroky Zadání → Kontrola údajů → Plán a cena v hlavičce zakázky.

- Stavy kroku: čeká (číslo v obrysu `border-strong`), aktivní (číslo na `primary`, název `ink` 600), hotovo (fajfka `success`), neaktuální (ikona přepočtu `stale` a slovo „neaktuální“), nedostupný (`ink-subtle`, nelze kliknout).
- Hotové kroky jsou odkazy zpět, aktivní má `aria-current="step"`.
- Pod 1280 px kompaktní tvar: ikony hotových kroků a název jen u aktivního.

### `SolutionStatusBadge`

Stav řešení plánu. Vždy ikona + slovo, volitelně podtext.

| Stav | Tokeny | Text | Podtext |
|---|---|---|---|
| `optimal` | `success` | Optimální | — |
| `best_found` | `info` | Nejlepší nalezený | vzdálenost od dolní meze, pokud je známá („nejvýš o 1 tyč víc než dolní mez“) |
| `partial` | `warning` | Částečný | počet neumístěných kusů |
| `infeasible` | `danger` | Bez řešení | důvod |
| `stale` | `stale` | Neaktuální | důvod („čekají nepotvrzené změny“) |

„Optimální“ se zobrazí jen tehdy, když ho backend prokáže (AGENTS.md pravidlo 9).

### `EditableGrid`

Kontrolní tabulka dílů a skladových délek v kroku Kontrola údajů. Chování v `behaviors/grid-navigation`: šipky mezi buňkami, Enter edituje a potvrdí, Esc vrátí původní hodnotu, Tab přejde dál, Enter na posledním řádku přidá řádek, vložení více řádků ze schránky.

- Sloupce dílů: Název, Délka (mm), Počet (ks), u skladových délek Délka, Cena za kus (Kč). Akce řádku: ✕ odebrat. Pod tabulkou „+ Přidat díl“.
- Prázdný stav: jeden prázdný řádek s placeholdery („např. sloupek“).
- Stavy buňky:
  - **potvrzená**: běžný vzhled;
  - **nepotvrzená** (výchozí hodnota nebo odhad modelu): přerušovaný okraj `proposal` 1 px, ikona `?` v `proposal`, tooltip s původem („Výchozí hodnota, ověřte“, „Odhad AI z textu ‚šestimetrové‘“);
  - **změněná návrhem**: podklad `proposal-bg`, původní hodnota přeškrtnutá v `ink-muted`, nová v `ink`;
  - **chybná**: okraj `danger`, ikona a text chyby pod buňkou nebo v tooltipu a v souhrnu nad tabulkou.
- Stavy řádku: **nový z návrhu** (podklad `proposal-bg`, štítek `Badge proposal` „nový“), **odebraný návrhem** (přeškrtnutý, akce „Vrátit“).
- Načítání (návrh se aktualizuje): tabulka ztlumená, jen ke čtení, nad ní pruh s `Loader`.
- Pod tabulkou trvalá legenda: „? nepotvrzená hodnota (výchozí nebo odhad AI), potvrdí se tlačítkem Potvrdit a vypočítat“.

### `ValidationSummary` a `ChangeSummary`

- `ValidationSummary` (`Alert danger`, `review/ValidationSummary.svelte`): „Opravte 2 pole, než spustíte výpočet“ a seznam chyb jako odkazy, které přesunou fokus na pole. Pole nese `data-cell` s klíčem z view modelu (`target`: `parts.1.length_mm`, `parameters.objective`); u chyby celé tabulky dostane fokus první buňka, u cíle vybraná volba. Chyba bez pole ve formuláři zůstane textem. U prázdného ručního zadání se souhrn ani chyby buněk neukazují, dokud uživatel nezačne vyplňovat.
- Převod jednotek v buňce délky („1,5 m“ → 1 500 mm) oznámí stavový řádek „Převedeno: 1,5 m = 1 500 mm.“ (`role=status`).
- Krok Kontrola údajů bez návrhu (zakázka je potvrzená): `EmptyState` „Údaje jsou potvrzené“ s akcí „Upravit údaje“ (`primary`). Stejná akce (`secondary`) je v záhlaví kroku Plán a cena.
- `ChangeSummary` (rámeček s přerušovaným okrajem `proposal`, podklad `proposal-bg`): „Změny oproti verzi 2“ a seznam změn („+ 2× příčka 850 mm“, „sloupek: 2 000 → 2 200 mm“). Akce „Potvrdit a vypočítat“ (`primary`) a „Zahodit změny“ (`ghost`) jsou v patičce kroku, ne ve shrnutí.

### `MetricCard`

Popisek stylem `small` v `ink-muted`, hodnota stylem `metric` s jednotkou v `ink-muted`, volitelný podtext. Karty v mřížce, stejná výška. Sada pro 1D: Spotřebované tyče, Délka dílů, Využitelné zbytky, Odpad, Výtěžnost; při skladu Ze skladu, K nákupu. Hodnota, která chybí, je „—“ s vysvětlením, nikdy 0.

### `CuttingPlan1D`

Měřítkový plán tyčí. SVG generuje backend (`render_svg`), frontend ho vloží a přidá interakci (zvýraznění dílu). Vizuální pravidla jsou v `plan-rezani.md`.

### `CostBreakdown`

Panel kalkulace: řádky Materiál, Práce, Další náklady (popis vlevo, částka vpravo s `numeric`), součty Náklady, Přirážka, Základ, DPH, oddělovač a **Celkem** stylem `heading`. Pod tím „Předpoklady“ stylem `small`.

- Neúplná kalkulace: `Badge warning` „Neúplná“, chybějící položka „chybí cena“ v `warning` s akcí „Doplnit cenu“; nikdy `0 Kč`. Celkem má poznámku „bez chybějících položek“.
- Čeká na plán: obsah ztlumený, text „Kalkulace se spočítá z plánu“.
- Vstupy kalkulace (hodiny a sazba práce, další náklady, přirážka, DPH) se upravují přímo v panelu přes `NumberUnitInput` a plán nezneplatní (specifikace kap. 4, pravidlo R2 ze service designu). Změněná hodnota se ihned promítne do součtů; ceny skladových délek patří ke vstupům plánu.

### `StaleBanner`

Pruh přes celou šířku nad plánem na `stale-bg` s ikonou přepočtu: „Neaktuální: čekají nepotvrzené změny (+ 2× příčka 850 mm)“ a akce „Zkontrolovat změny“ nebo „Přepočítat“ (`primary`). Plán pod ním je ztlumený (průhlednost 50 %), ztlumené jsou i metriky, cena a štítek kvality, a tisk plánu je neaktivní s důvodem v tooltipu.

### `ResultSummaryBar`

Lišta připnutá dole v kroku Plán a cena: `SolutionStatusBadge`, souhrn („5 tyčí · výtěžnost 91,7 % · celkem 7 166,23 Kč“) a akce Vytisknout plán (`secondary`, jen u aktuálního výsledku) a Uložit zakázku (`primary`). Stáhnout PDF přibude s kalkulací (M5); do té doby se nenabízí. Tisk (`@media print`) dá papír k pile na A4: název a materiál, plán, cena materiálu a celý rozpis po tyčích bez ovládacích prvků. Varianty: počítá se, neúplná kalkulace, neaktuální (cena přeškrtnutá, akce „Zkontrolovat změny“), částečný („1 kus neumístěn“, akce „Upravit díly“), plán není spočítaný (akce „Vypočítat“).

### `ChatMessage`

| Druh | Vzhled |
|---|---|
| uživatel | vpravo, podklad `surface-sunken`, `rounded-md` |
| asistent | vlevo, bez podkladu, text `ink` |
| systémová poznámka | uprostřed, `small` `ink-muted` („Nástroj: Řezání tyčí“) |
| průběh | `Loader`, fáze s přelivem textu („Připravuji údaje…“) a „Zrušit“ |
| chyba | `Alert danger` v historii s akcemi „Zkusit znovu“, „Zadat ručně“ |
| otázka | text a `Chip` s volbami |
| nepodporované zadání | text a nabídka podporovaných nástrojů |
| návrh změny | rámeček s přerušovaným okrajem `proposal` na `proposal-bg`, štítek „Návrh“, seznam změn a odkaz „Zobrazit v kontrole“; potvrzuje se v kroku Kontrola údajů, ne ve zprávě |
| vysvětlení výsledku | text, ve kterém jsou čísla odkazy na místo v plánu („zvýrazněno v plánu“) |

Posouvání historie řídí `behaviors/message-scroller` (drží pozici při čtení starších zpráv, posune na novou zprávu, jen když je uživatel dole).

### `ChatComposer`, `SuggestionChips`, `ChatRail`

- `ChatComposer`: víceřádkové pole (Enter odešle, Shift+Enter nový řádek) a tlačítko Odeslat. Během zpracování je odeslání neaktivní a vedle je „Zrušit“.
- `SuggestionChips`: řada `Chip` nad polem (ukázky zadání, rychlé úpravy).
- `ChatRail`: sbalený dialog jako pruh 44 px s ikonou a tečkou nepřečtené zprávy.

### Úvodní obrazovka

- `HeroPrompt`: velké `TextArea` s ukázkou zadání v placeholderu, „Další ukázka“ (`ghost`) a „Pokračovat“ (`primary`).
- `ToolCard`: karta nástroje (název, jedna věta) jako tlačítko; rozšíření jen když jsou implementovaná.
- `ResumeCard`: rozpracovaná zakázka s krokem a akcí „Pokračovat v zakázce“.
- `ExampleList`: seznam příkladů v modálním okně, šipky a Enter.

### Rozšíření (jen pokud budou implementována)

`StockMatchInfo`, `PurchaseList`, `PendingChangesBar`, `UnplacedPiecesAlert` a 2D plán. Navrhnou se spolu s rozšířením ve stejném vizuálním jazyce.

## Odchylky od low-fi prototypu

- Nový řádek z návrhu je v prototypu zelený; zde má barvu `proposal`, protože ještě neplatí. Zelená `success` je vyhrazená pro potvrzený a optimální stav.
- Změněná hodnota je v prototypu žlutá; zde `proposal-bg`, aby žlutá zůstala jen pro upozornění.
- Nepotvrzená hodnota: prototyp používá přerušovaný rámeček a `?`, mapa obrazovek tečkované podtržení. Platí přerušovaný rámeček a `?` (shodně s návrhem změny: přerušovaná čára = ještě neplatí).
- Odebraný řádek s „Vrátit“ platí i v kroku Kontrola údajů, nejen ve skladu.
- U nespočítaného plánu ukazuje `ResultSummaryBar` „Plán není spočítaný“, ne „Neaktuální“.
