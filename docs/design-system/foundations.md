# Foundations

Hodnoty tokenů jsou v [`tokens.css`](tokens.css); tento dokument říká, co znamenají a kdy je použít. V Tailwindu se tokeny používají přímo názvem: `bg-surface`, `text-ink-muted`, `border-border-strong`, `text-heading`, `rounded-md`, `shadow-overlay`. Výchozí paleta a stupnice Tailwindu jsou vypnuté, takže `bg-gray-100` ani `text-lg` nefungují.

Systém má jen světlý režim. Plán a PDF jsou na světlém podkladu, primárním zařízením je notebook v dílně nebo kanceláři.

## Barvy

### Plochy a text

| Token | Hodnota | Použití |
|---|---|---|
| `page` | `#f6f5f2` | podklad stránky za panely |
| `surface` | `#ffffff` | panely, karty, tabulky, modální okna |
| `surface-sunken` | `#efede8` | záhlaví tabulek, hover řádků a položek menu |
| `border` | `#ddd9d0` | vlasové linky: okraje panelů, oddělovače řádků (dekorativní) |
| `border-strong` | `#8c8679` | okraj vstupních polí a zaškrtávátek |
| `ink` | `#1d1b18` | hlavní text a čísla |
| `ink-muted` | `#5c574e` | vedlejší text, popisky polí, jednotky za číslem |
| `ink-subtle` | `#6f695f` | placeholder, nejméně důležité popisky |

Neutrální odstíny jsou mírně zahřáté k jantarové, aby plocha nepůsobila jako výchozí šedá.

### Akcent

| Token | Hodnota | Použití |
|---|---|---|
| `primary` | `#f2b220` | výplň jediné hlavní akce v panelu, značka aktuálního kroku |
| `primary-hover` | `#e3a30f` | hover a stisk hlavní akce |
| `on-primary` | `#1d1b18` | text a ikony na `primary`; nikdy bílá |
| `accent-text` | `#a14f06` | jantar jako text nebo čára: odkaz, aktivní záložka, číslo aktuálního kroku |
| `focus-ring` | `#1d1b18` | fokus: linka 1 px těsně kolem prvku |
| `focus-halo` | `#f2b220` na 55 % | fokus: jantarová záře 3 px vně linky (dekorativní) |

Světlá jantarová na bílé nemá kontrast pro text ani čáru, proto se jako text a obrys používá tmavší `accent-text`. Fokus je grafitová linka s jantarovou září: viditelnost nese linka (kontrast přes 14:1), záře dává fokusu charakter značky.

### Stavy

Každý stav má dvojici text a podklad a vždy i ikonu a slovo. Barva stav jen podporuje.

| Význam | Text a ikona | Podklad | Ikona a text navíc |
|---|---|---|---|
| Optimální plán, úspěšné potvrzení | `success` `#0b6b5f` | `success-bg` `#e3f2ef` | fajfka, „Optimální“ |
| Nejlepší nalezený plán, průběh, informace | `info` `#1f5a8f` | `info-bg` `#e6eff8` | kroužek s i nebo `Loader`, „Nejlepší nalezený“ |
| Částečný plán, chybějící cena, upozornění | `warning` `#8a4b00` | `warning-bg` `#fbf0dc` | trojúhelník, „Částečný“ |
| Chyba, neplatné pole, bez řešení | `danger` `#b42318` | `danger-bg` `#fbeae8` | kroužek s křížkem, „Bez řešení“ |
| Neaktuální výsledek | `stale` `#5c574e` | `stale-bg` `#eceae5` | šipky přepočtu, ztlumení plánu, „Neaktuální“ |
| Nepotvrzená hodnota, návrh změny od AI | `proposal` `#3f4fb8` | `proposal-bg` `#eef0fb` | přerušovaná čára, ikona „?“, „Návrh“ |

`success` je posunutá k modrozelené, aby se od `danger` nelišila jen odstínem na ose červená–zelená.

### Plán řezání

| Token | Hodnota | Použití |
|---|---|---|
| `plan-part-1` … `plan-part-8` | `#9fc4e8` `#a3d6c4` `#c6dc9e` `#d7bce4` `#f0bba6` `#b9c4da` `#e7c6d2` `#bfe0e8` | barva typu dílu: proužek nahoře na dílu, výplň zvýrazněného dílu, legenda; od 9. typu se opakují |
| `plan-bar` | `#efede8` | podklad skladové tyče |
| `plan-cut` | `#a14f06` | řezná značka: čára, trojúhelník a poloha řezu v mm |
| `plan-remnant` | `#dcefe1` | využitelný zbytek, popisek v `success` |
| `plan-waste` | `#f1efea` | podklad odpadu |
| `plan-waste-hatch` | `#7d776c` | šrafa odpadu pod 45° |
| `plan-kerf` | `#1d1b18` | prořez v rozpisu a legendě PDF |
| `plan-highlight` | `#a14f06` | obrys zvýrazněného dílu 2 px |

Jantarová `primary` se v plánu nepoužívá, aby se díl nepletl s akcí. Pravidla plánu jsou v [`plan-rezani.md`](plan-rezani.md).

### Ověření kontrastu

Spočítáno vzorcem WCAG 2 (relativní jas). Text vyžaduje 4,5:1, okraje ovládacích prvků, fokus a grafické značky 3:1.

| Dvojice | Kontrast | Požadavek |
|---|---|---|
| `ink` na `page` / `surface` / `surface-sunken` | 15,8 / 17,2 / 14,7 | 4,5 ✓ |
| `ink-muted` na `page` / `surface` / `surface-sunken` | 6,6 / 7,2 / 6,1 | 4,5 ✓ |
| `ink-subtle` na `page` / `surface` / `surface-sunken` | 5,0 / 5,4 / 4,7 | 4,5 ✓ |
| `border-strong` na `surface` / `page` | 3,6 / 3,3 | 3 ✓ |
| `on-primary` na `primary` / `primary-hover` | 9,1 / 7,8 | 4,5 ✓ |
| `accent-text` na `surface` / `page` | 5,8 / 5,3 | 4,5 ✓ |
| `focus-ring` na `surface` / `page` / `surface-sunken` / `primary` | 17,2 / 15,8 / 14,7 / 9,1 | 3 ✓ |
| `success` na `success-bg` / `surface` | 5,6 / 6,4 | 4,5 ✓ |
| `info` na `info-bg` / `surface` | 6,2 / 7,2 | 4,5 ✓ |
| `warning` na `warning-bg` / `surface` | 6,0 / 6,8 | 4,5 ✓ |
| `danger` na `danger-bg` / `surface` | 5,7 / 6,6 | 4,5 ✓ |
| `stale` na `stale-bg` | 6,0 | 4,5 ✓ |
| `proposal` na `proposal-bg` / `surface` | 6,1 / 7,0 | 4,5 ✓ |
| `ink` na `plan-part-1` … `plan-part-8` | 9,4 až 12,3 | 4,5 ✓ |
| `ink` na `plan-remnant` / `plan-waste` | 14,3 / 15,0 | 4,5 ✓ |
| `plan-cut` na `surface` / `plan-bar` | 5,8 / 4,9 | 4,5 ✓ |
| `success` na `plan-remnant` | 5,3 | 4,5 ✓ |
| `plan-waste-hatch` na `plan-waste` | 3,9 | 3 ✓ |
| `plan-highlight` na výplních dílů a zbytku | 3,2 až 4,8 | 3 ✓ |

`border` (1,4:1) je jen dekorativní oddělovač; žádný ovládací prvek se jím neohraničuje. Při změně barvy se kontrast přepočítá a tabulka aktualizuje.

## Typografie

Písmo je **IBM Plex Sans**, ve vývojářském panelu **IBM Plex Mono**. Plex vznikl pro inženýrské prostředí, má plnou českou diakritiku a tabulární číslice. Aplikace běží bez sítě, proto se písmo přibalí do frontendu (`@fontsource/ibm-plex-sans`, řezy 400, 500, 600; `@fontsource/ibm-plex-mono` 400) a nenačítá se z Google Fonts.

| Styl | Velikost / řádek | Řez | Použití |
|---|---|---|---|
| `display` | 28 / 36 px, −0,01 em | 600 | jen název na úvodní obrazovce |
| `title` | 20 / 28 px | 600 | název zakázky v hlavičce |
| `heading` | 16 / 24 px | 600 | nadpis panelu a sekce |
| `body` | 14 / 20 px | 400 | výchozí text, zprávy, buňky tabulek |
| `body` + `font-semibold` | 14 / 20 px | 600 | tlačítka, součty, zvýraznění |
| `small` | 13 / 18 px | 400 | nápověda pod polem, tooltip, popisky metrik |
| `label` | 12 / 16 px, +0,04 em, velká písmena | 500 | záhlaví sloupců, legenda, štítky stavu |
| `metric` | 24 / 32 px | 600 | hodnota metriky; vždy s `numeric` |
| `code` | 13 / 18 px, mono | 400 | jen vývojářský panel |

- Každé číslo v tabulce, metrice nebo součtu má utilitu `numeric` (tabulární číslice) a v tabulce je zarovnané vpravo.
- Číslo se sází v `ink`, jednotka za ním v `ink-muted`, mezi nimi nezlomitelná mezera.
- Řádek souvislého textu má nejvýš asi 70 znaků; nadpisy mají `text-wrap: balance`.
- Kurzíva se nepoužívá; zdůraznění je řezem 600.

## Rozestupy

Mřížka 4 px, shodná s výchozí stupnicí Tailwindu. Používají se jen kroky v tabulce.

| Krok | Hodnota | Použití |
|---|---|---|
| 1 | 4 px | ikona a text, číslo a jednotka |
| 2 | 8 px | mezi poli v řádku, vnitřní odsazení štítku a buňky |
| 3 | 12 px | vnitřní odsazení tlačítka a zprávy, mezi zprávami |
| 4 | 16 px | vnitřní odsazení panelu a karty, mezera mezi kartami metrik |
| 6 | 24 px | mezi sekcemi v panelu, mezi dialogem a pracovní plochou |
| 8 | 32 px | mezi hlavními bloky stránky |
| 12 | 48 px | svislý rytmus úvodní obrazovky |

## Zaoblení, okraje, stíny

- `rounded-sm` (4 px): vstupní pole, štítky, buňky, díly v plánu (v SVG 2 px).
- `rounded-md` (6 px): tlačítka, karty metrik, zprávy dialogu.
- `rounded-lg` (8 px): panely, modální okna, menu.
- Kulaté tvary („pilulky“) se nepoužívají.
- Hierarchii nesou okraje `border`, ne stíny. `shadow-raised` mají jen panely nad `page`, `shadow-overlay` jen menu, tooltip, popover a modální okno.

## Pohyb

- Pohyb jen vysvětluje změnu, nezdobí.
- `--duration-fast` (120 ms) pro hover a fokus, `--duration-base` (200 ms) pro otevření panelu, menu a příchod zprávy; křivka `ease-standard`.
- Výsledek po přepočtu se neanimuje, jen se vymění.
- Načítání ukazuje `Loader` (tyč plněná díly, cyklus 1,8 s), ne spinner.
- Při `prefers-reduced-motion: reduce` jsou obě délky 0 ms, `Loader` stojí se dvěma vloženými díly a text zůstává.

## Fokus a přístupnost

- Každý ovládací prvek má viditelný fokus: linka `focus-ring` 1 px a záře `focus-halo` 3 px (`box-shadow`, sleduje zaoblení prvku), definovaný globálně v `tokens.css`. Splňuje WCAG 2.4.7 (AA); přísnější 2.4.13 (AAA, obrys aspoň 2 px) nesplňuje, jde o vědomou volbu vzhledu.
- Okraj ovládacího prvku má aspoň 3:1 (`border-strong`); text aspoň 4,5:1.
- Stav a význam nikdy jen barvou: vždy i text, ikona nebo vzor (šrafa, přerušovaná čára).
