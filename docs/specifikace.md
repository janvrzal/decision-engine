# DecisionEngine — specifikace cílové verze pro semestrální práci

**Verze:** 0.2.1 — rozsah po první diskuzi, kap. 10 sladěna se zněním zadání  
**Datum:** 23. 11. 2026  
**Stav:** Specifikace budoucího chování; tento dokument nepopisuje dokončenou implementaci.

**Změny oproti 0.1:** 2D řezání je volitelné rozšíření, nikoli povinná funkce. Nově je jako rozšíření zařazen sklad materiálu včetně zbytků. Fotky jako vstup jsou mimo semestr. Projekt vzniká v novém repozitáři. Kalkulace je oddělená od záměru `cost_estimate`. Uživatel volí cíl optimalizace. 1D solver používá generování vzorů (column generation). Router je vyměnitelný: Jev, Layo, LLM nebo ruční výběr.

**Oprava 0.2.1:** Kapitola 10 odkazuje na znění zadání v `docs/zadani.md` (téma 2) a uvádí i povinný požadavek na uživatelské rozhraní.

## 1. Produkt a jeho účel

DecisionEngine je webová aplikace pro malé dílny a řemeslníky. Z přirozeného zadání pomůže vytvořit ověřenou zakázku, vybrat vhodný výpočet a získat použitelný výrobní podklad a orientační kalkulaci.

Uživatel může napsat například: „Na plot potřebuji deset jeklů po dvou metrech a pět příček po metru a půl, nakupuji šestimetrové tyče.“ Aplikace rozpozná typ úlohy, připraví údaje ke kontrole, vypočítá nářezový plán a nabídne jeho export. Uživatel může navázat: „Přidej ještě dvě příčky a přepočítej cenu.“ Pokud je zapnutý sklad, může napsat: „Použij nejdřív zbytky ze skladu a zbytek dokup.“

Hlavní přínos: méně ručního přepisování, přehledné plánování materiálu a možnost upravovat zakázku bez opakovaného zadávání všech údajů.

## 2. Cíloví uživatelé

| Uživatel | Potřeba | Typická situace |
|---|---|---|
| Zámečník nebo malá kovodílna | Rozdělit požadované délky do skladových tyčí | Plot, rám, regál, konstrukce |
| Truhlář nebo domácí dílna | Rozmístit pravoúhlé díly na desky (rozšíření) | Police, jednoduchá skříň, pracovní stůl |
| Majitel malé dílny | Odhadnout náklady a využít zbytky z dřívějších zakázek | Příprava nabídky zákazníkovi |

Semestrální verze cílí na samostatně pracujícího uživatele v češtině, na notebooku nebo desktopu. Nevyžaduje týmovou spolupráci ani napojení na podnikový systém.

## 3. Rozsah odevzdávané verze

Jádro tvoří 1D plánování, kalkulace, dialog a router. Na tomto jádru stojí dvě volitelná rozšíření. Obě se přidávají jako nové schopnosti v registru (kap. 7) a jádro na nich nezávisí.

### Povinné funkce

| Oblast | Cílové chování |
|---|---|
| Vstup | České textové zadání a plně použitelný ruční formulář |
| Směrování | Router vybírá z implementovaných schopností; uživatel může volbu změnit |
| Strukturovaná extrakce | Generativní LLM převádí zadání do validovaného schématu příslušné úlohy |
| Dialog | Navazující změny využívají potvrzená data aktuální zakázky |
| Kontrola | Upravitelná tabulka a výslovné potvrzení před výpočtem |
| 1D plánování | Řezání tyčí s prořezem, více skladovými délkami, uživatelem zvoleným cílem optimalizace a rozlišením odpadu a využitelného zbytku |
| Kalkulace | Materiál podle spotřebovaných tyčí, uživatelem zadaná práce a další náklady |
| Výsledek | Vizualizace, rozpis dílů, materiálové metriky a stav řešení |
| Uložení | Export a import zakázky v JSON včetně potvrzených vstupů a nastavení |
| Export | PDF plánu a orientační kalkulace |
| Dostupnost | Spustitelná webová aplikace, ukázkové zakázky a demo režim bez API |

### Volitelná rozšíření (cílová, podmíněná)

Rozšíření se začnou stavět až po dokončení povinných funkcí. Pokud čas nestačí na obě, má přednost to, které bude mít v danou chvíli lepší poměr přínosu a rizika. Nedokončené rozšíření se v aplikaci nezobrazí jako dostupný nástroj.

| Rozšíření | Cílové chování |
|---|---|
| 2D plánování | Rozmístění pravoúhlých dílů na jeden formát desky s možností použít více desek a s ověřeným gilotinovým postupem řezání (UC-02) |
| Sklad materiálu | Evidence dostupných tyčí a zbytků s počty; solver přednostně použije sklad a dokoupí jen chybějící materiál; využitelné zbytky z plánu lze po potvrzení zapsat zpět (UC-08) |

### Mimo rozsah semestru

- 3D balení do dodávky, kontejneru nebo na paletu.
- Obecný nesting nepravidelných tvarů a čtení CAD výkresů.
- Automatické získávání cen od dodavatelů.
- Fotografie, PDF a audio jako vstup (kandidát na rozvoj po semestru, kap. 13).
- Plné ERP: zakázky zákazníků, objednávky, nákup, příjemky, fakturace a platby.
- Účty a týmová spolupráce.
- Statické výpočty konstrukcí, posuzování bezpečnosti a soulad s normami.
- Záruka globálně optimálního řešení pro každou úlohu.

Tyto funkce se nebudou zobrazovat jako dostupné nástroje. Zadání vyžadující nepodporovanou schopnost dostane srozumitelnou odpověď a možnost přejít na podporovanou úlohu.

## 4. Podoba uživatelského rozhraní

### Úvodní obrazovka

- Název DecisionEngine a stručný popis: „Ze zadání k nářezovému plánu a ceně zakázky.“
- Hlavní textové pole s příklady českých zadání.
- Karty „Řezání tyčí“ a „Kalkulace“ pro přímý výběr; „Řezání desek“ a „Sklad“ jen tehdy, pokud je dané rozšíření implementováno.
- Tlačítka pro načtení zakázky a otevření připraveného příkladu.
- Dostupné demo se zřetelným označením, že používá připravená data.

### Pracovní obrazovka zakázky

Jedna zakázka má tři kroky: **Zadání → Kontrola údajů → Plán a cena**. Na široké obrazovce je dialog vlevo a pracovní plocha vpravo. Na menší obrazovce se panely řadí pod sebe.

Dialog zůstává dostupný i nad výsledkem. Obsahuje zprávy a stručná potvrzení změn. Rozměry, počty a ceny mají své vlastní editovatelné tabulky; důležité údaje nezůstávají pouze ve zprávách.

Uživatel vidí zvolený nástroj běžným názvem, například „Řezání tyčí“. Názvy modelů, použitý router, tokeny a interní diagnostika jsou dostupné v odděleném vývojářském panelu. Tam lze také přepnout implementaci routeru (kap. 6).

### Kontrola údajů

- Viditelné jednotky, názvy dílů a počty.
- Zvolený cíl optimalizace (kap. 6, UC-01).
- Zvláštní označení hodnot převzatých z výchozího nastavení nebo odhadnutých modelem.
- Konkrétní upozornění u neplatného pole.
- Souhrn změn při navazující úpravě zakázky.
- Jedno hlavní tlačítko „Potvrdit a vypočítat“.

### Výsledek

- Měřítkový plán tyčí (u rozšíření i desek) s popisky a legendou.
- Spotřebované tyče, délka požadovaných dílů, odpad a zbytky; při zapnutém skladu i rozdělení na „ze skladu“ a „k nákupu“.
- Výtěžnost jako poměr materiálu v hotových dílech ke spotřebovanému vstupnímu materiálu; využitelné zbytky se uvádějí samostatně.
- Viditelný stav: optimální, nejlepší nalezený, částečný nebo bez proveditelného řešení. U nejlepšího nalezeného řešení se uvádí i vzdálenost od dolní meze, pokud je známá.
- Kalkulace s uvedenými cenovými předpoklady a chybějícími položkami.
- Akce „Upravit“, „Přepočítat“, „Uložit zakázku“ a „Stáhnout PDF“.

Úprava vstupů označí původní výsledek jako neaktuální. Export plánu je dostupný až pro výsledek odpovídající potvrzené verzi vstupů.

## 5. Uživatelské scénáře

### UC-01: Vytvoření nářezového plánu tyčí

**Cíl:** Převést textový seznam dílů na použitelný plán řezání.

1. Uživatel zadá názvy, délky a počty dílů a dostupné skladové délky, případně jejich ceny.
2. Router vybere řezání tyčí, pokud uživatel nezvolil nástroj přímo.
3. Generativní model připraví strukturované údaje v milimetrech.
4. Aplikace ukáže tabulku dílů, skladové délky, prořez, minimální délku využitelného zbytku a cíl optimalizace.
5. Uživatel údaje opraví a potvrdí.
6. Solver vytvoří plán a aplikace zobrazí rozpis, metriky a export.

**Cíl optimalizace:** Uživatel volí jednu možnost z pevné nabídky:

| Cíl | Minimalizuje |
|---|---|
| Nejnižší cena materiálu | Součet cen spotřebovaných tyčí |
| Nejméně tyčí | Počet spotřebovaných tyčí |
| Nejméně materiálu | Součet délek spotřebovaných tyčí (tedy odpad a zbytky dohromady) |

Výchozí cíl je „nejnižší cena“, pokud jsou zadané ceny všech skladových délek, jinak „nejméně materiálu“. Výchozí volba je viditelně označena jako nepotvrzená. Zvolený cíl je součástí zakázky a ovlivňuje štítek „optimální“ (kap. 8).

**Účtování prořezu:** Každý řez spotřebuje šířku prořezu. Kapacitní podmínka tyče délky *L* s díly *l₁…lₙ* je Σ lᵢ + n·k ≤ L + k, kde *k* je prořez. Poslední řez tedy nepočítáme, pokud za posledním dílem nezůstane žádný materiál. Volitelný zarovnávací ořez začátku tyče se odečte od *L*.

**Zbytky:** Část tyče, která zbude po posledním dílu, je *využitelný zbytek*, pokud dosahuje alespoň uživatelem zadané minimální délky (parametr; výchozí hodnota je označená jako nepotvrzená). Jinak jde o *odpad*.

**Odchylky:** Chybějící skladová délka se vyžádá nebo nabídne jako výslovně nepotvrzená výchozí hodnota. Příliš dlouhé díly se vypíší samostatně; částečný plán se neprezentuje jako splněná zakázka. Cíl „nejnižší cena“ bez kompletních cen se nespustí; aplikace nabídne doplnění cen nebo jiný cíl.

**Úspěch:** Každý požadovaný kus je zahrnut právě jednou nebo výslovně označen jako neumístěný.

### UC-02: Rozmístění dílů na desky (rozšíření)

**Cíl:** Získat prostorově platný plán pro pravoúhlé díly.

1. Uživatel uvede šířky, délky a počty dílů a formát desky.
2. Aplikace vyžádá prořez, okrajový ořez a případné omezení otáčení dílů.
3. Uživatel potvrdí tabulku a nastavení.
4. Solver rozmístí díly na jednu nebo více desek stejného formátu.
5. Aplikace ukáže každou desku, polohy dílů, spotřebu a využití plochy.

**Omezení:** Jedna úloha obsahuje jeden materiál, jednu tloušťku a jeden formát vstupní desky. Rotace je pouze o 90° a lze ji zakázat pro konkrétní díl, například kvůli směru dekoru. Nepravidelné tvary nejsou podporovány.

**Proveditelnost řezání:** Cílová implementace používá gilotinové dělení: každý řez prochází přes celý právě zpracovávaný obdélníkový kus. Výstup zahrnuje pořadí řezů. Pokud vznikne pouze geometrické rozmístění bez ověřeného postupu řezání, musí být označeno jako rozložení dílů, nikoli výrobní nářezový plán. Solver je heuristický; výsledek se označuje jako „nejlepší nalezené“, pokud nejde o triviálně dokazatelný případ (například počet desek rovný dolní mezi z plochy).

**Úspěch:** Díly nepřesahují použitelnou oblast, nepřekrývají se, respektují prořez, povolenou orientaci a deklarovaný postup řezání.

### UC-03: Navazující změna zakázky

**Příklad:** „Přidej dvě příčky délky 850 mm a ostatní nech stejné.“

1. Aplikace předá modelu aktuální potvrzenou zakázku a novou zprávu.
2. Model navrhne změnu strukturovaných dat.
3. Aplikace zobrazí změněné řádky a zachová ostatní hodnoty.
4. Uživatel změnu potvrdí a spustí nový výpočet.

**Odchylky:** „Prodluž to o deset“ vyvolá doplňující otázku na díl a jednotku. Neplatná změna nesmí přepsat poslední validní zakázku.

**Úspěch:** Změna je dohledatelná, nedochází ke ztrátě předchozích údajů a starý výsledek je označen jako neaktuální.

### UC-04: Orientační kalkulace

**Cíl:** Vyčíslit náklady na zakázku z plánu a vlastních cen.

1. Uživatel doplní cenu každé skladové délky za tyč (u rozšíření 2D cenu desky za kus).
2. Doplní odhad hodin práce, hodinovou sazbu a další paušální náklady.
3. Aplikace vypočítá materiál podle skutečně použitých tyčí/desek, práci a ostatní náklady.
4. Volitelně přičte uživatelem zadanou přirážku k nákladům a sazbu DPH.
5. Zobrazí rozpad a zahrne jej do exportu.

Přirážka znamená procento z nákladů, nikoli marži z prodejní ceny. Sazby ani ceny aplikace sama nevymýšlí. Chybějící cena znamená neúplnou kalkulaci, nikoli nulový náklad. Peněžní výpočty používají desetinnou aritmetiku (`Decimal`) a jednotné zaokrouhlování. Výstup je orientační kalkulace, ne faktura.

Při zapnutém skladu se materiál ze skladu oceňuje evidovanou cenou skladové položky. Uživatel může zvolit, že se skladový materiál do kalkulace nezapočítá (například již zaplacené zbytky); tato volba se uvádí mezi cenovými předpoklady.

**Úspěch:** Každá částka je odvoditelná ze zobrazených vstupů a po změně plánu se materiálové náklady aktualizují.

### UC-05: Nejasné nebo nepodporované zadání

**Příklady:** „Chci vyrobit skříň.“ / „Naskládej tyto bedny do dodávky.“

1. Router vrátí nejasné zadání nebo nepodporovanou úlohu.
2. Aplikace nabídne výběr nástroje nebo zformuluje jednu konkrétní doplňující otázku.
3. Uživatel upřesní zadání nebo přejde na ruční výběr.

**Úspěch:** Aplikace nespustí nesouvisející solver a neslibuje dosud neimplementované 3D řešení.

### UC-06: Uložení a pokračování

1. Uživatel exportuje zakázku do JSON.
2. Později soubor načte.
3. Aplikace ověří verzi formátu a strukturu a obnoví vstupy, nastavení, cíl optimalizace a ceny.
4. Uživatel pokračuje v úpravách a plán znovu vypočítá.

**Úspěch:** Import nevyžaduje API volání. Soubor obsahuje vše potřebné pro obnovení zakázky a neobsahuje API klíče. Historie dialogu není pro obnovu povinná. Stav skladu není součástí zakázky; ukládá se samostatně (UC-08).

### UC-07: Práce při výpadku AI

1. Volání AI selže nebo je vyčerpána kvóta.
2. Aplikace zachová rozepsané zadání a platná data a nabídne opakování, přepnutí na lokální router (Layo) či ruční vstup.
3. Uživatel dokončí výpočet a export bez vzdálené AI.

**Úspěch:** Selhání routeru ani parseru nezablokuje funkční výpočetní moduly. Demo je dostupné i bez připojení k poskytovatelům AI.

### UC-08: Využití skladu a zbytků (rozšíření)

**Cíl:** Spotřebovat nejdřív materiál, který dílna má, a dokoupit jen chybějící.

1. Uživatel vede seznam skladových položek: materiál/profil, délka, počet a volitelně cena za kus. Zbytky z dřívějších zakázek jsou běžné položky s příznakem „zbytek“.
2. Při zadání zakázky může napsat „použij, co je na skladě“ nebo zapnout volbu v kontrole údajů.
3. Solver pracuje se dvěma zdroji: omezené počty ze skladu a neomezený nákup standardních délek.
4. Výsledek rozliší tyče ze skladu a tyče k nákupu.
5. Po potvrzení výroby aplikace nabídne odečíst spotřebované položky ze skladu a zapsat nové využitelné zbytky. Teprve toto potvrzení stav skladu mění.

**Odchylky:** Pokud uživatel zakáže nákup a sklad nestačí, úloha je bez proveditelného úplného řešení; aplikace ukáže částečný plán s neumístěnými kusy a nabídne povolení nákupu. Shoda materiálu mezi zakázkou a skladem se kontroluje podle identifikátoru materiálu/profilu, nikoli podle volného textu.

**Úspěch:** Výpočet nikdy nepoužije více kusů, než je na skladě. Sklad se nezmění bez výslovného potvrzení. Každá změna skladu je dohledatelná (kdy, z jaké zakázky, jaké položky).

## 6. Role AI a řízení toku

### Router: výběr schopnosti a uživatelského záměru

Router dostává aktuální zprávu, stručný stav zakázky a popisy dostupných schopností. Pro výběr typu úlohy používá pevnou množinu možností:

- `cutting_1d`
- `cutting_2d` (jen pokud je rozšíření implementováno)
- `cost_estimate`
- `unclear`
- `unsupported`

Samostatnou otázkou může rozlišovat novou zakázku, úpravu současné zakázky a dotaz k výsledku. Odpovědi na více otázek aplikace kontroluje společně; jednotlivé otázky samy nezaručují vzájemně konzistentní výstup.

`cost_estimate` je **záměr** („chci cenu“), nikoli samostatný výpočet. Při existujícím plánu otevře jeho kalkulaci. Bez plánu aplikace nabídne ruční položky materiálu nebo nejprve vytvoření plánu. Samotný výpočet ceny je společná služba (kap. 7). Explicitní výběr nástroje uživatelem má přednost před routerem.

Při nejistém nebo rozporném výsledku se aplikace doptá. Prahy se nastaví podle testů na českých zadáních. Pravděpodobnost ani confidence nenahrazují validaci. Router vybírá schopnost; konkrétní solver, jeho parametry a spuštění určuje aplikační logika.

### Implementace routeru

Router je rozhraní s vyměnitelnými implementacemi. Volba je v nastavení a vývojářském panelu a zaznamenává se do `RoutingDecision`.

| Implementace | Popis | Role |
|---|---|---|
| `JevRouter` | TypeSafe Jev přes API, primitivum Choice; vrací volbu, pravděpodobnosti všech možností a confidence | Výchozí, pokud obstojí v evaluaci |
| `LayoRouter` | Open-weight varianta Jev spouštěná lokálně (~0,5 GB RAM) | Offline provoz, demo a záloha při výpadku API |
| `LlmRouter` | Generativní LLM se strukturovaným výstupem omezeným na stejnou množinu možností | Srovnávací varianta a záloha |
| `ManualRouter` | Výběr nástroje uživatelem | Vždy dostupný |

Všechny implementace vracejí stejný typ `RoutingDecision`. Stejná evaluační sada (kap. 9) se spouští na každé dostupné implementaci a výsledky se porovnávají v reportu.

### Generativní model: extrakce a dialog

- Vytváří vstupy podle schématu vybrané schopnosti.
- Navrhuje změny nad potvrzenou verzí zakázky.
- Formuluje otázky k chybějícím údajům.
- U zapnutého skladu může navrhnout použití skladových položek; výběr konkrétních kusů ale provádí solver.
- Může vysvětlit výsledek z dodaných metrik; nové číselné závěry musí pocházet z výpočtu.

Povinná pole, jednotky a fyzická omezení kontroluje kód. Po neúspěšné validaci se návrh neuloží jako potvrzená zakázka. Seznam chybějících povinných polí se odvozuje ze schématu, nikoli pouze z názoru modelu.

### Paměť kontextu

Zdrojem pravdy jsou strukturovaná data zakázky a její revize. Historie zpráv pomáhá s interpretací odkazů typu „ty příčky“, ale nenahrazuje potvrzené údaje. Nová zakázka začíná s prázdným kontextem. V jedné relaci lze vrátit poslední nepotvrzený návrh změny.

## 7. Architektura

Aplikace vzniká od nuly v novém repozitáři. Žádný kód z dřívějších pokusů se nepřebírá.

```mermaid
flowchart TD
    U[Text nebo přímý výběr nástroje] --> R[Router: Jev / Layo / LLM / uživatel]
    R --> P[LLM: extrakce a návrh změn]
    P --> V[Validace a kontrola uživatelem]
    M[Ruční formulář] --> V
    V --> S[Výpočetní modul]
    W[(Sklad – rozšíření)] -.-> S
    S -.-> W
    S --> C[Služba kalkulace]
    S --> O[Vizualizace a PDF]
    C --> O
    V --> J[Uložení a načtení zakázky]
```

### Vrstvy: funkcionální jádro, imperativní obal

| Vrstva | Obsah | Pravidla |
|---|---|---|
| Jádro | Datové objekty, validace, solvery, kalkulace, použití potvrzené změny na zakázku a na sklad | Čisté funkce bez I/O, času a náhody; neměnná data (Pydantic `frozen=True`, kolekce jako `tuple`); chyby se vracejí jako hodnoty, nevyhazují se |
| Adaptéry | Routery (Jev, Layo, LLM), generativní model, čtení a zápis JSON, úložiště skladu, PDF | Jediné místo se závislostí na konkrétním poskytovateli; ven vracejí jen validované objekty jádra nebo chybu |
| UI | Streamlit | Drží stav relace, volá jádro a adaptéry a nic samo nepočítá |

**Chyby jako hodnoty a Pydantic:** Pydantic při neplatných datech vyhazuje `ValidationError`. Jádro proto vytváří objekty přes tenký obal (např. `parse(model, data) -> Ok[T] | Err[list[FieldError]]`), který výjimku zachytí a převede na seznam chyb po jednotlivých polích. Výjimky tak nepřekročí hranici jádra a chyby polí lze přímo zobrazit v kontrolní tabulce. Stejně se obalují výjimky solverů (například OR-Tools).

Díky tomuto rozdělení jde jádro testovat jednotkovými testy bez sítě a bez API klíče. Stejné jádro používá i ruční formulář a demo režim, takže výpadek AI (UC-07) se týká jen adaptérů.

### Schopnosti a služby

Výpočty jsou v registru schopností. Každá schopnost deklaruje identifikátor, popis pro router, vstupní schéma, formulář, validaci, výpočet a prezentaci výsledku. Povinná verze obsahuje schopnost `cutting_1d`. Rozšíření `cutting_2d` a sklad se přidají jako nové záznamy v registru bez zásahu do ostatních.

**Kalkulace je služba, ne schopnost.** Vstupem je normalizovaný seznam spotřebovaného materiálu (`MaterialConsumption`: položka, počet, zdroj – nákup/sklad), ceny, práce, další náklady, přirážka a DPH. Nezáleží jí na tom, zda seznam pochází z 1D plánu, 2D plánu nebo z ručně zadaných položek. Záměr `cost_estimate` z routeru jen otevírá kalkulaci v UI (kap. 6).

### 1D solver

Solver řeší úlohu řezání tyčí (cutting stock) s více skladovými délkami, prořezem a uživatelem zvoleným cílem (UC-01). Postup:

1. **Okamžitá heuristika.** First Fit Decreasing rozšířený pro více délek: díly se seřadí sestupně; při otevírání nové tyče se vybere skladová délka s nejlepším poměrem podle zvoleného cíle (cena nebo délka na spotřebovaný milimetr) pro díly, které se do ní vejdou. Výsledek slouží jako platné záložní řešení a horní mez.
2. **Generování vzorů (Gilmore–Gomory column generation).** Vzor řezání je kombinace dílů, která se vejde do jedné tyče dané délky. LP relaxace hlavní úlohy určuje, kolikrát který vzor použít; pomocná úloha batohu (knapsack) pro každou skladovou délku hledá vzor se zápornou redukovanou cenou. Postup končí, když žádný takový vzor neexistuje. Hodnota LP relaxace dává **dolní mez**.
3. **Celočíselné řešení.** Z nalezených vzorů se vybere celočíselná kombinace pomocí CP-SAT (OR-Tools) s časovým limitem, nastartovaná řešením z heuristiky.
4. **Štítek.** Pokud se hodnota řešení rovná zaokrouhlené dolní mezi, je řešení prokazatelně optimální. Jinak je „nejlepší nalezené“ a UI uvede rozdíl od dolní meze.

Rozšíření o sklad (UC-08) přidá horní meze na počet použitých tyčí dané skladové položky; struktura postupu se nemění. Pomocná úloha batohu i hlavní úloha musí respektovat identitu dílů a jejich počty.

Přímý model „kus × tyč“ v CP-SAT se nepoužívá: kvůli symetrii (zaměnitelné tyče) obvykle neprokáže optimum ani u středně velkých úloh. Pevná hranice „malé úlohy“ podle počtu kusů se proto nezavádí; o štítku rozhoduje prokázaná dolní mez a časový limit (kap. 8).

### 2D solver (rozšíření)

Heuristika s gilotinovým dělením volného prostoru (např. gilotinová varianta MaxRects / shelf s více strategiemi řazení), která přímo vytváří strom řezů. Výsledek se označuje jako „nejlepší nalezené“, pokud počet desek nedosáhne dolní meze danou plochou.

### Stav zakázky

Stav zakázky je její poslední potvrzená revize. LLM ani solver do ní nezapisují přímo: LLM vytvoří `ChangeProposal`, uživatel ho v kontrolní tabulce potvrdí nebo opraví, a teprve potom jádro z předchozí revize a potvrzené změny vytvoří novou revizi. Výsledek výpočtu nese číslo revize, ze které vznikl, takže je vidět, kdy už neodpovídá aktuálním vstupům.

Sklad má vlastní revize a vlastní úložiště. Výsledek výpočtu se skladem nese i revizi skladu; změna skladu označí výsledek jako neaktuální.

### Technické rozhodnutí

Python 3.12 a Streamlit. Optimalizace přes OR-Tools (LP pro relaxaci, CP-SAT pro celočíselnou část). Sklad se ukládá lokálně (SQLite nebo JSON soubor), bez serverové databáze. Přechod na jiný frontend není součástí semestrální verze. Má smysl až při potřebě účtů, týmové práce nebo složitější interakce s plánem.

### Hlavní datové objekty

| Objekt | Obsah |
|---|---|
| `Project` | ID, název, verze formátu, typ úlohy, potvrzená revize |
| `Problem` | Materiál, požadované díly a vstupní formáty specifické pro modul |
| `Parameters` | Prořez, zarovnávací ořez, minimální délka využitelného zbytku, cíl optimalizace, použití skladu a časový limit; u 2D i omezení rotace a okrajový ořez |
| `ChangeProposal` | Základní revize a navržené změny čekající na potvrzení |
| `CalculationResult` | Stav řešení, vstupní revize (a revize skladu), umístění dílů, metriky, dolní mez a neumístěné kusy |
| `MaterialConsumption` | Normalizovaný seznam spotřebovaného materiálu pro kalkulaci, se zdrojem nákup/sklad |
| `CostEstimate` | Ceny materiálu, práce, další náklady a cenové předpoklady |
| `StockItem` | Materiál/profil, délka (u desek rozměry), počet, cena, příznak zbytku, původ (rozšíření) |
| `StockChange` | Potvrzená změna skladu s odkazem na zakázku a revizi (rozšíření) |
| `RoutingDecision` | Implementace routeru, vybraná schopnost, pravděpodobnosti, confidence, verze modelu a případný důvod náhradního postupu |

## 8. Spolehlivost a provoz

- API klíče jsou v serverovém prostředí; neukládají se do zakázek, exportů ani diagnostických záznamů.
- UI rozlišuje chybu připojení, vyčerpaný limit a neplatná data a nabízí odpovídající další krok.
- Opakování dočasně neúspěšných volání je omezené; aplikace neběží v nekonečné smyčce. (SDK TypeSafe ve výchozím stavu opakuje odpověď `429` podle `retry-after`; počet opakování se omezí.)
- Cache AI odpovědí zahrnuje relevantní stav zakázky, model, implementaci routeru a verzi extrakčního schématu/promptu.
- Každý výpočet má časový limit (výchozí 10 s, nastavitelný). Po jeho dosažení se vrátí nejlepší platné řešení, pokud existuje; heuristika zaručuje, že nějaké platné řešení existuje vždy, když je úloha proveditelná bez omezení skladu.
- Označení „optimální“ se používá pouze při prokázaném optimu pro deklarovaný model a **zvolený cíl** (UC-01) – u 1D na základě dolní meze z LP relaxace. Jinak UI uvádí „nejlepší nalezené řešení“ a rozdíl od dolní meze.
- Zachovává se identita dílů i při shodných rozměrech.
- Schéma zaručuje tvar dat; správnost přepisu uživatelského zadání vyžaduje kontrolu a testování.
- Vývojářská diagnostika ukazuje čas, použitý model a router, stav validace, rozhodnutí routeru a u solveru počet vzorů, dolní mez a stav CP-SAT, bez tajných údajů.

Pro demo sady do přibližně 100 kusů u 1D a 30 kusů u 2D je cílem výpočet do 10 sekund na dokumentovaném referenčním stroji. Jde o cíl k ověření; latence externí AI se měří zvlášť.

## 9. Kritéria přijetí a ověření

| Oblast | Podmínka dokončení |
|---|---|
| Router | Na oddělené sadě alespoň 50 ručně označených českých zadání dosáhne výchozí implementace alespoň 90 % správných voleb včetně `unclear` a `unsupported`; report obsahuje chyby podle kategorií a srovnání všech dostupných implementací (Jev, Layo, LLM) |
| Extrakce | Na alespoň 30 jednoznačných zadáních 1D dosáhne alespoň 90 % úplné shody kritických polí: rozměry, počty, jednotky a vstupní formáty (u rozšíření 2D samostatná sada) |
| Neúplné vstupy | Připravené případy s chybějícími povinnými údaji neprojdou k výpočtu bez doplnění nebo výslovného potvrzení nabídnuté hodnoty |
| Dialog | Nejméně 10 scénářů o třech a více uživatelských kolech ověří přidání, odebrání, změnu a nejasný odkaz bez ztráty ostatních dat |
| 1D solver | Kontroly ověří počty kusů, kapacity, účtování prořezu a klasifikaci zbytků; pro každý cíl optimalizace se malé úlohy porovnají s nezávisle ověřeným řešením (např. úplné prohledání); štítek „optimální“ se objeví jen při dosažení dolní meze |
| Kalkulace | Ručně ověřené příklady pokryjí více cen tyčí, práci, přirážku, zaokrouhlení a neúplné ceny |
| Stav | Změna vstupů nezanechá starý plán prezentovaný jako aktuální a nepotvrzený návrh nepřepíše platná data |
| Import/export | Uložená a znovu načtená zakázka zachová vstupy včetně cíle optimalizace; neplatný soubor zobrazí srozumitelnou chybu |
| PDF | Text, diakritika, legendy a popisky jsou čitelné; delší zakázka se nerozbije při stránkování |
| Výpadek AI | Ruční zadání, výpočet a export fungují bez dostupného vzdáleného routeru i generativního modelu |
| Použitelnost | Alespoň tři lidé mimo vývoj projektu vyzkouší vytvoření a změnu zakázky; blokující problémy budou opraveny a poznatky stručně popsány |
| 2D solver *(pokud je rozšíření součástí odevzdání)* | Kontroly ověří hranice, nepřekrývání, prořez, rotace, počty a platnost deklarované posloupnosti řezů |
| Sklad *(pokud je rozšíření součástí odevzdání)* | Testy ověří, že plán nepřekročí skladové počty, sklad se bez potvrzení nezmění, odečtení a zápis zbytků odpovídají plánu a nedostatečný sklad bez nákupu vede k částečnému plánu |

Sady pro ladění promptů a měření výsledků musí být oddělené. U AI části report uvádí model, verzi, implementaci routeru, datum a podmínky měření; metriky nejsou obecnou zárukou přesnosti.

## 10. Splnění zadání předmětu

Projekt řeší téma 2 „Vytvoření středně složité aplikace“; plné znění je v [`docs/zadani.md`](zadani.md). Zadání vyžaduje vlastní uživatelské rozhraní s důrazem na použitelnost a vizuální čistotu a alespoň 2 ze 4 dalších požadavků.

| Kritérium | Povinnost | Doložení v cílové aplikaci |
|---|---|---|
| Vlastní UI, pěkné a dobře použitelné | povinné | Streamlit podle kap. 4: tři kroky zakázky, editovatelné tabulky, měřítkový plán, srozumitelné stavy a chyby |
| Strukturovaný výstup / function calling | 2 ze 4 | LLM extrakce do schématu a následná validace; router navíc vrací typovanou volbu |
| Vícekolový dialog nebo více LLM rolí | 2 ze 4 | Kontextové změny aktuální zakázky; dialog je hlavní důkaz tohoto kritéria |
| Propojení LLM s výpočtem nebo datovým zdrojem | 2 ze 4 | Výpočet nářezového plánu a kalkulace nad potvrzenými daty a vlastními cenami; u rozšíření i práce se skladem jako datovým zdrojem |
| Multimodalita na vstupu | 2 ze 4 | Není součástí semestrální verze |

Cílová aplikace tedy pokrývá tři ze čtyř volitelných kritérií (požadovány jsou dvě). Protože TypeSafe vymezuje Jev (System One) jako odlišnou kategorii od generativních LLM, splnění požadavků nestojí pouze na jeho klasifikaci. Hlavními doklady jsou generativní extrakce, kontextový dialog a propojení s výpočty.

Projekt vzniká v novém repozitáři během semestru; celá historie repozitáře tedy dokládá práci provedenou v rámci předmětu.

## 11. Doporučené pořadí realizace

1. **Postavit 1D jádro:** datové objekty, validace s chybami jako hodnotami, heuristika a generování vzorů, metriky, revize a aktuálnost výsledku, import/export, ruční formulář.
2. **Ověřit router:** hned na začátku vyzkoušet Jev v Playgroundu a Layo lokálně na několika českých zadáních (podpora češtiny není v dokumentaci uvedena); podle výsledku zvolit výchozí implementaci.
3. **Přidat dialog a router:** extrakce, směrování, změny zakázky, doptávání a náhradní ruční postup.
4. **Doplnit kalkulaci:** služba nad `MaterialConsumption`, explicitní ceny, práce a návaznost na spotřebu materiálu.
5. **Dokončit povinný produkt:** PDF, demo, evaluace routeru a extrakce. Tímto bodem je odevzdatelná verze hotová.
6. **Rozšíření:** sklad (UC-08) a/nebo 2D (UC-02), podle zbývajícího času. Sklad je menší a navazuje na hotový 1D solver; 2D je větší a samostatnější.
7. **Uzavřít:** uživatelské zkoušky, report a dokumentace spuštění.

Odevzdaná verze bez rozšíření pokrývá všechna požadovaná AI kritéria. Nedokončené rozšíření se nesmí prezentovat jako hotové.

## 12. Scénář obhajoby

1. Otevřít aplikaci a zadat zakázku na řezání jeklů přirozeným jazykem.
2. Ukázat zvolený nástroj, rozpoznané údaje, cíl optimalizace a potvrzení vstupů.
3. Vypočítat plán (se štítkem optimální / nejlepší nalezené) a doplnit vlastní ceny materiálu a práce.
4. Napsat „Přidej dvě příčky po 850 mm“, potvrdit změnu a ukázat nový plán i cenu.
5. Ukázat nejasné zadání a doptání místo nesouvisejícího výpočtu.
6. Přepnout router (Jev / Layo / LLM) a ukázat srovnání z evaluace.
7. *Pokud je hotové:* „Použij nejdřív zbytky ze skladu“ – plán se skladem a nákupem, zápis nových zbytků.
8. *Pokud je hotové:* úloha na desky s omezením rotace a 2D výsledkem.
9. Exportovat PDF a obnovit uloženou zakázku.

K obhajobě bude připravený i offline demo režim (lokální Layo nebo připravená data). Připravená data budou označená a nebudou vydávána za živé volání modelu.

## 13. Další rozvoj po semestru

- **Fotky a PDF jako vstup:** fotografie nářezového seznamu nebo náčrtu s kótami převedená do stejného schématu zakázky (Jev již čte PNG/JPEG; extrakci by obstaral generativní model).
- **3D balení pravoúhlých beden do jednoho typu prostoru.** Před implementací se samostatně vymezí orientace, stohovatelnost, nosnost, podpora jednotlivých kusů a přístup při nakládání. Geometrické umístění samo o sobě neprokazuje bezpečnost nákladu.
- **Rozšíření směrem k ERP:** zakázky zákazníků, nákupní seznamy a objednávky, příjem materiálu na sklad.
- Spotřeba obkladů/podlah, plánování pracovních operací, import kusovníků.

Každá schopnost dostane vlastní smlouvu vstupů, omezení, výpočet a ověření. Router nabízí pouze skutečně implementované schopnosti.

## 14. Referenční zdroje pro integraci routeru

- [TypeSafe — úvod a typy rozhodnutí](https://docs.typesafe.ai/introduction)
- [Choice — výběr z pevné množiny možností](https://docs.typesafe.ai/primitives/choice)
- [System One — schopnosti a omezení](https://docs.typesafe.ai/concepts/system-one)
- [Modely, ceny a jazyková podpora](https://docs.typesafe.ai/models)
- [Python SDK](https://docs.typesafe.ai/sdk/python)

Stav ověřený 23. 11. 2026 z dokumentace TypeSafe:

- Aktuální model je `jev-1.14.0` (alias `jev-latest`), předchozí `jev-1.13.0`.
- Choice vrací zvolenou možnost, pravděpodobnost každé možnosti (součet 1) a `confidence` 0–1; přijme až 255 možností.
- Python SDK: balíček `typesafe-sdk`, Python 3.10+, klíč v proměnné `TYPESAFE_API_KEY`; API klíč a Playground v konzoli console.typesafe.ai.
- Cena: 0,042 USD za milion vstupních tokenů, výstupní tokeny zdarma.
- Kontext: 64k na požadavek, 32k na otázku.
- **Neuvedeno v dokumentaci:** podpora češtiny, bezplatný tarif nebo zkušební kredit, konkrétní rate limity a model Layo. Údaje o Layo (open-weight varianta Jev, lokální běh, ~0,5 GB RAM) pocházejí od autora projektu a je třeba je ověřit při instalaci.

Konkrétní model, dostupnost a ceny je nutné znovu ověřit při implementaci; nejsou pevnou součástí produktové specifikace.
