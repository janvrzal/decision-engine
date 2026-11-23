# Vizuální jazyk plánu řezání

Plán je hlavní výsledek aplikace a výrobní podklad: uživatel ho čte na obrazovce a nese v PDF k pile. Zvolená varianta je **„Řezné značky“**: díly jsou neutrální, typ dílu nese barevný proužek a u každého řezu je jeho poloha měřená od začátku tyče. U pily tak stačí svinovací metr, není potřeba sčítat délky a prořezy.

Plán vykresluje backend čistou funkcí `render_svg` (ADR-0007); stejné SVG se zobrazí v UI i v PDF. Frontend ho jen vloží a přidá zvýraznění dílu. Barvy jsou tokeny `plan-*` z [`tokens.css`](tokens.css); backend má jejich kopii a test hlídá, že se shodují.

Zvažované varianty, porovnané nad stejnou zakázkou: barevné díly s popisky (nejrychlejší orientace, ale bez poloh řezů), technický výkres s kótami (přesný, ale na obrazovce nepřehledný), kompaktní řádky s textovým rozpisem (pro mnoho tyčí, ale čte se jako seznam) a zvolené řezné značky.

## Prvky

| Prvek | Vzhled | Tokeny |
|---|---|---|
| Řádek souhrnu nad plánem | „6 tyčí po 6 000 mm · prořez 3 mm · polohy řezů od začátku tyče“ | `ink-muted`, `small` |
| Skupina tyčí | vlevo počet stejných tyčí („4×“, 14 px, 600) a jejich čísla („Tyč 1–4“, 11 px) | `ink`, `ink-muted` |
| Tyč | obdélník výšky 26 px, zaoblení 2 px | `plan-bar`, obrys `border-strong` |
| Díl | bílá výplň s obrysem, nahoře proužek 5 px v barvě typu; popisek „Název délka“ uprostřed | `surface`, `border-strong`, `plan-part-n`, text `ink` |
| Řez | čára 1,5 px přes celou výšku tyče, nad ní trojúhelník a poloha řezu v mm (11 px, 600) | `plan-cut` |
| Využitelný zbytek | výplň úseku, popisek „zbytek 4 497“ | `plan-remnant`, text `success` |
| Odpad | šrafa pod 45° po 6 px, délka v tooltipu a v rozpisu | `plan-waste`, `plan-waste-hatch` |
| Legenda | pod plánem: typy dílů (název, délka, počet), řez, využitelný zbytek s prahem, odpad | vzorky stejných tokenů |
| Rozpis po tyčích | sbalitelná tabulka (`DataTable`): tyč, díly, polohy řezů, zbytek nebo odpad | textová alternativa plánu |

## Pravidla

**Měřítko a uspořádání**

- Všechny tyče jsou v jednom měřítku podle nejdelší skladové délky; plán vyplní šířku panelu, pod 560 px se posouvá do strany ve vlastním kontejneru.
- Stejné tyče se seskupí do jednoho řádku („4×“); skupiny jsou seřazené od nejčastější, při shodě podle pořadí ve výsledku solveru.
- Svislý rozestup mezi tyčemi je 34 px, aby se nad tyč vešly polohy řezů.

**Popisky a čísla**

- Čísla ve formátu `cs-CZ` s nezlomitelnou mezerou („4 003“); jednotka mm je v řádku souhrnu a v legendě, ne u každého čísla.
- Popisek dílu: „Název délka“ od 110 px šířky, jen délka od 40 px, užší díl jen s tooltipem.
- Poloha řezu je souřadnice začátku prořezu od začátku tyče. Leží-li dvě polohy blíž než 48 px, druhá se posune o řádek (14 px) výš.
- Barva typu nikdy nenese informaci sama: díl má popisek nebo tooltip a legenda uvádí název, délku a počet kusů.

**Zbytek a odpad**

- Zbytek od prahu (výchozí 300 mm, nastavitelný) je využitelný zbytek; kratší je odpad. Práh je uvedený v legendě.
- Prořez se nekreslí jako samostatný úsek; jeho šířku nese čára řezu a řádek souhrnu.

**Stavy**

| Stav | Zobrazení |
|---|---|
| hotovo | plán, legenda, `SolutionStatusBadge` v záhlaví panelu |
| zvýrazněný díl | všechny výskyty typu se vyplní barvou typu a dostanou obrys `plan-highlight` 2 px; spouští najetí na díl, řádek tabulky nebo číslo ve zprávě dialogu |
| počítá se | velký `Loader` a „Hledám lepší plán…“, nejlepší dosavadní plán pod ním ztlumený |
| neaktuální | `StaleBanner` nad plánem, plán ztlumený na 50 %, bez zvýrazňování, export PDF neaktivní |
| prázdný | `EmptyState` „Plán zatím není spočítaný“ s akcí „Vypočítat“ |
| částečný | plán umístěných kusů a nad ním `Alert warning` „Neumístěné kusy“ s důvodem |

**Přístupnost**

- SVG má `role="img"`, `title` („Nářezový plán: 6 tyčí po 6 000 mm, prořez 3 mm“) a `desc` se souhrnem každé skupiny včetně poloh řezů.
- Díly, řezy, zbytky a odpad mají vlastní `title` (tooltip).
- Rozpis po tyčích je plnohodnotná textová alternativa a ovládá se klávesnicí.

## PDF

- Stejné SVG ve stejných barvách; světlé výplně a šrafa zůstávají čitelné i v černobílém tisku (řez je čára s číslem, typ dílu má popisek).
- Plán se láme po celých skupinách tyčí, nikdy uprostřed tyče; legenda je na každé stránce s plánem.
- Pod plánem je vždy rozpis po tyčích s polohami řezů.

## Rozšíření

2D plán desek a sklad převezmou stejné tokeny a pravidla (proužek typu, řez s polohou, zbytek a odpad). Navrhnou se, až budou rozšíření implementovaná.
