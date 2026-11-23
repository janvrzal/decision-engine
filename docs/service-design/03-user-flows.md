# User flows

**Stav:** schváleno  
**Vychází z:** [02-use-cases.md](02-use-cases.md) (pravidla R1–R6, katalog událostí), specifikace v0.3 kap. 4 a 7, ADR-0006

Každý tok má diagram a tabulku kroků. Diagramy F0–F10 jsou i na FigJam boardu (odkaz v README) a stavy jednotlivých panelů zachycují sekce H–K tamtéž. Tabulka uvádí obrazovku nebo panel (podle [slovníku](README.md#slovník-obrazovek-a-panelů)), rozhodovací body, prázdné a chybové stavy a události reduceru. Hvězdička (*) označuje událost navrženou v katalogu use cases.

**Legenda diagramů**

- obdélník = obrazovka, panel nebo krok, který uživatel vidí
- kosočtverec = rozhodnutí (uživatele nebo aplikace)
- zaoblený obdélník = práce na pozadí (AI, solver, PDF), během ní stav načítání
- šestiúhelník = chybový stav
- popisek hrany = událost reduceru nebo akce uživatele

| Tok | Obsah | UC |
|---|---|---|
| [F0](#f0-stavy-zakázky) | Stavy zakázky (stavový diagram) | všechny |
| [F1](#f1-hlavní-tok) | Hlavní tok: zadání → kontrola → plán a cena → úprava dialogem → přepočet → export | 01, 03, 04 |
| [F2](#f2-zpracování-zprávy-v-dialogu) | Zpracování zprávy v dialogu (router a záměry) | 01, 03, 05, 14, 15 |
| [F3](#f3-výpadek-ai) | Výpadek AI a obnova | 07 |
| [F4](#f4-vstupy-do-aplikace) | Vstupy do aplikace: první spuštění, příklad, načtení, nová zakázka | 06, 09, 10, 13, 15 |
| [F5](#f5-kalkulace) | Kalkulace a export PDF | 04 |
| [F6](#f6-demo-režim) | Demo režim | 11 |
| [F7](#f7-vývojářský-panel) | Vývojářský panel | 12 |
| [F8](#f8-řezání-desek-rozšíření) | Řezání desek *(rozšíření)* | 02 |
| [F9](#f9-sklad-v-zakázce-rozšíření) | Sklad v zakázce a zápis zbytků *(rozšíření)* | 08 |
| [F10](#f10-správa-skladu-rozšíření) | Správa skladu *(rozšíření)* | 16 |

---

## F0: Stavy zakázky

Stavový diagram shrnuje, v jakém stavu může být zakázka v relaci. Je to pohled na `AppState`, ne samostatné pole: stavy se odvozují z potvrzené revize, čekajícího návrhu, výsledku a běžících efektů (R3). Pracovní plocha zobrazuje krok podle tohoto stavu.

```mermaid
stateDiagram-v2
    [*] --> Prazdna: SessionStarted*
    Prazdna --> Zpracovani: MessageSent
    Prazdna --> Navrh: ToolSelected* (ručně)
    Prazdna --> Navrh: ProjectImported*
    Zpracovani --> Navrh: ProposalReceived
    Zpracovani --> Prazdna: ClarificationReceived* / AiFailed (bez zakázky)
    Navrh --> Navrh: ProposalEdited*
    Navrh --> Vypocet: ProposalConfirmed
    Navrh --> PlanAktualni: ProposalRejected (plán existoval)
    Navrh --> Potvrzena: ProposalRejected (plán neexistoval)
    Vypocet --> PlanAktualni: SolveFinished
    Vypocet --> Potvrzena: SolveFailed* / OperationCancelled*
    Potvrzena --> Vypocet: SolveRequested
    PlanAktualni --> PlanAktualni: CostInputsChanged*
    PlanAktualni --> Zpracovani: MessageSent (úprava)
    PlanAktualni --> Navrh: ProposalEdited*
    PlanAktualni --> PlanNeaktualni: změna skladu
    PlanNeaktualni --> Vypocet: SolveRequested
    Zpracovani --> PlanAktualni: ExplanationReceived* / ClarificationReceived*
    PlanAktualni --> [*]: NewProjectRequested*

    Prazdna: Prázdná zakázka
    Zpracovani: Zpracovávám zprávu (AI)
    Navrh: Čeká návrh ke kontrole
    Potvrzena: Potvrzená, bez plánu
    Vypocet: Výpočet běží
    PlanAktualni: Plán aktuální
    PlanNeaktualni: Plán neaktuální
```

| Stav | Krok na pracovní ploše | Plán | Hlavní akce |
|---|---|---|---|
| Prázdná zakázka | Zadání | — | Odeslat zadání / Zadat ručně |
| Zpracovávám zprávu | beze změny, průběh v Panelu Dialog | beze změny | Zrušit |
| Čeká návrh ke kontrole | Kontrola údajů | pokud existuje, je **neaktuální** (R3) | Potvrdit a vypočítat |
| Potvrzená, bez plánu | Plán a cena (prázdný stav s vysvětlením) | — | Vypočítat |
| Výpočet běží | Plán a cena (načítání) | předchozí neaktuální | Zrušit |
| Plán aktuální | Plán a cena | aktuální | Upravit, Uložit zakázku, Stáhnout PDF |
| Plán neaktuální | Plán a cena | neaktuální | Přepočítat |

Stav „Čeká návrh ke kontrole“ nad existujícím plánem je v diagramu stejný uzel jako u nové zakázky. Liší se jen tím, že souhrn změn má s čím porovnávat.

---

## F1: Hlavní tok

Tok, který prochází end-to-end test (spec. kap. 9, „UI – hlavní tok“) a scénář obhajoby.

```mermaid
flowchart TD
    A["Úvodní obrazovka"] -->|"MessageSent"| B(["F2: router a extrakce"])
    A -->|"ToolSelected* (ručně)"| D
    B -->|"ProposalReceived"| D["Krok Kontrola údajů: tabulky, parametry, cíl"]
    B -->|"otázka / chyba"| B2["Panel Dialog: doplňující otázka nebo chyba (F2, F3)"]
    B2 -->|"odpověď uživatele"| B
    D -->|"ProposalEdited*"| D
    D --> E{"Návrh platný a úplný?"}
    E -->|"ne"| E1{{"Chyby po polích, tlačítko neaktivní"}}
    E1 -->|"oprava"| D
    E -->|"ano: Potvrdit a vypočítat"| F(["Výpočet: ProposalConfirmed, RunSolver"])
    F -->|"OperationCancelled*"| F1["Plán a cena: výpočet zrušen, Přepočítat"]
    F -->|"SolveFailed*"| F2{{"Plán a cena: chyba výpočtu, Zkusit znovu"}}
    F -->|"SolveFinished"| G["Krok Plán a cena: Panel Plán + Panel Kalkulace"]
    F1 -->|"SolveRequested"| F
    F2 -->|"RetryRequested*"| F
    G -->|"CostInputsChanged*"| G
    G -->|"zpráva v Panelu Dialog (MessageSent)"| B
    G -->|"Upravit"| D
    G --> H{"Plán aktuální?"}
    H -->|"ano"| I["Stáhnout PDF / Uložit zakázku"]
    H -->|"ne"| J["Přepočítat"]
    J -->|"SolveRequested"| F
```

| # | Krok | Obrazovka / panel | Rozhodnutí | Prázdný / chybový stav | Události |
|---|---|---|---|---|---|
| 1 | Zadání | Úvodní obrazovka nebo Krok Zadání | text, nebo karta nástroje | prázdné pole s ukázkami zadání; „Odeslat“ neaktivní, dokud je pole prázdné | `MessageSent`, `ToolSelected`* |
| 2 | Rozpoznání a extrakce | Panel Dialog (průběh), Pracovní plocha beze změny | router: typ a záměr (F2) | nejasné → otázka; chyba AI → F3 | `RoutingDecided`*, `ProposalReceived` |
| 3 | Kontrola | Krok Kontrola údajů | je návrh platný a úplný? cíl „nejnižší cena“ má všechny ceny? | chyby po polích, seznam chyb nad tabulkou; nepotvrzené hodnoty označené | `ProposalEdited`* |
| 4 | Potvrzení | Krok Kontrola údajů | — | — | `ProposalConfirmed` |
| 5 | Výpočet | Krok Plán a cena, Panel Plán (načítání, „Zrušit“) | — | zrušení, chyba solveru | `SolveRequested`, `SolveFinished`, `SolveFailed`*, `OperationCancelled`* |
| 6 | Plán a cena | Panel Plán, Panel Kalkulace | stav řešení: optimální / nejlepší nalezené / částečný / bez řešení | částečný: seznam neumístěných kusů; kalkulace: „chybí cena“ | `CostInputsChanged`* |
| 7 | Úprava dialogem | Panel Dialog → Krok Kontrola údajů se souhrnem změn | potvrdit / upravit / zahodit | plán viditelně neaktuální, PDF neaktivní | `MessageSent`, `ProposalReceived`, `ProposalRejected` |
| 8 | Přepočet | jako krok 4–6 | — | — | `ProposalConfirmed`, `SolveFinished` |
| 9 | Export | Panel Plán / Hlavička zakázky | je plán aktuální? | neaktuální: „Stáhnout PDF“ neaktivní s vysvětlením | `PdfRequested`*, `PdfRendered`* |

**Ukazatel kroků** v hlavičce ukazuje Zadání → Kontrola údajů → Plán a cena. Hotové kroky jsou klikací. Když čeká návrh, krok Plán a cena má štítek „neaktuální“, ale lze se na něj podívat.

---

## F2: Zpracování zprávy v dialogu

Co se stane po odeslání libovolné zprávy v Panelu Dialog. Rozhodování o záměru dělá aplikační logika podle `RoutingDecision`, ne frontend.

```mermaid
flowchart TD
    M["Zpráva odeslána (MessageSent)"] --> X{"Uživatel zvolil nástroj ručně?"}
    X -->|"ano"| EX
    X -->|"ne"| R(["CallRouter: Rozpoznávám úlohu..."])
    R -->|"AiFailed"| F3{{"F3: výpadek AI"}}
    R -->|"RoutingDecided*"| T{"Typ úlohy a jistota"}
    T -->|"unclear / nízká confidence / rozpor"| Q["Panel Dialog: jedna otázka + karty nástrojů"]
    T -->|"unsupported"| U["Panel Dialog: co umím + karty nástrojů"]
    T -->|"cutting_1d / cutting_2d / cost_estimate"| I{"Záměr"}
    I -->|"nová zakázka, žádná neexistuje"| EX(["CallExtractor: nová zakázka"])
    I -->|"nová zakázka, existuje jiná"| NZ{"Začít novou zakázku?"}
    NZ -->|"ano"| EX
    NZ -->|"ne"| W["Zpráva se bere jako úprava"]
    W --> EC
    I -->|"úprava zakázky"| EC(["CallExtractor: změna proti potvrzené verzi"])
    I -->|"dotaz k výsledku"| EP(["CallExplainer*"])
    I -->|"cost_estimate"| CE{"Existuje plán?"}
    CE -->|"ano"| CP["Panel Kalkulace s navrženými hodnotami k potvrzení"]
    CE -->|"ne"| CN["Panel Dialog: Nejdřív vytvořit plán / Zadat materiál ručně"]
    EX -->|"ProposalReceived"| K["Krok Kontrola údajů"]
    EC -->|"ProposalReceived"| K
    EX -->|"ClarificationReceived*"| Q
    EC -->|"ClarificationReceived*"| Q
    EX -->|"AiFailed"| F3
    EC -->|"AiFailed"| F3
    EP -->|"ExplanationReceived*"| A["Panel Dialog: odpověď s odkazy na metriky"]
    EP -->|"AiFailed"| F3
    Q -->|"odpověď"| M
    Q -->|"klik na kartu (ToolSelected*)"| EX
    U -->|"klik na kartu (ToolSelected*)"| K2["Krok Kontrola údajů (prázdný návrh)"]
```

| Rozhodovací bod | Kdo rozhoduje | Poznámka |
|---|---|---|
| Nástroj zvolený ručně | uživatel | má přednost před routerem (spec. kap. 6) |
| Typ úlohy a jistota | router + práh v aplikační logice | práh z evaluace; confidence nenahrazuje validaci |
| Záměr | router (samostatná otázka) | nová zakázka / úprava / dotaz k výsledku |
| Začít novou zakázku? | uživatel | chrání rozpracovanou zakázku (UC-15 A1) |
| Existuje plán? | aplikační logika | pro `cost_estimate` (UC-04 A2) |

**Stavy Panelu Dialog během toku:** načítání má text podle fáze („Rozpoznávám úlohu…“, „Připravuji údaje ke kontrole…“, „Hledám odpověď…“) a tlačítko „Zrušit“ (`OperationCancelled`*). Pole pro zprávu zůstává editovatelné, ale odeslání čeká na dokončení. Prázdný Panel Dialog na začátku zakázky ukazuje 2–3 ukázky zpráv, nad plánem ukázky úprav („Přidej…“, „Změň délku…“).

---

## F3: Výpadek AI

```mermaid
flowchart TD
    S(["Volání AI (router, extrakce, vysvětlení)"]) -->|"AiFailed"| K{"Druh chyby"}
    K -->|"připojení"| C{{"Nepodařilo se spojit se službou AI"}}
    K -->|"limit"| L{{"Vyčerpaný limit služby AI"}}
    K -->|"neplatná odpověď"| N{{"AI vrátila nepoužitelná data"}}
    C --> O["Akce: Zkusit znovu / Zadat ručně / Lokální rozpoznávání"]
    L --> O2["Akce: Zadat ručně / Lokální rozpoznávání"]
    N --> O
    O -->|"RetryRequested*"| P{"Překročen počet opakování?"}
    P -->|"ne"| S
    P -->|"ano"| O2
    O -->|"ToolSelected*"| H["Krok Kontrola údajů (UC-13)"]
    O2 -->|"ToolSelected*"| H
    O -->|"RouterSwitched* (Layo)"| S
    O2 -->|"RouterSwitched* (Layo)"| S
```

- Text zprávy se po chybě vrátí do pole a nic se neztratí. Potvrzená zakázka a rozpracovaný návrh se nemění.
- „Lokální rozpoznávání“ se nabízí, jen když je Layo dostupné. Pomáhá jen s výběrem nástroje. Extrakce potřebuje generativní model, takže po přepnutí na Layo aplikace otevře ruční Kontrolu údajů s předvoleným nástrojem.
- Chyba se zobrazuje jako zpráva v Panelu Dialog (ne jako toast), aby zůstala v historii a nesla akce.

---

## F4: Vstupy do aplikace

```mermaid
flowchart TD
    S["Spuštění aplikace (SessionStarted*)"] --> B{"Backend dostupný?"}
    B -->|"ne"| BE{{"Celostránková chyba: spusťte server, Zkusit znovu"}}
    BE --> S
    B -->|"ano"| H["Úvodní obrazovka"]
    H --> AI{"AI nastavená (klíč Groq)?"}
    AI -->|"ne"| HN["Textové pole neaktivní s vysvětlením; karty, příklady, demo a načtení fungují"]
    AI -->|"ano"| HA["Textové pole aktivní s ukázkami"]
    HA -->|"MessageSent"| F2(["F2"])
    H -->|"karta nástroje (ToolSelected*)"| K["Krok Kontrola údajů, prázdný návrh"]
    H -->|"Otevřít příklad"| EXD["Dialog Příklady"]
    EXD -->|"ExampleOpened*"| R{"Rozpracovaná zakázka s neuloženými změnami?"}
    H -->|"Načíst zakázku"| IMD["Dialog Načíst zakázku"]
    IMD -->|"soubor vybrán"| V{"Soubor platný?"}
    V -->|"ne"| VE{{"Chyba v dialogu: co je špatně"}}
    VE --> IMD
    V -->|"částečně (neplatné hodnoty)"| KE["Krok Kontrola údajů s chybami (UC-06 E2)"]
    V -->|"ano"| R
    R -->|"ne"| KI["Krok Kontrola údajů s načtenými daty (ProjectImported*)"]
    R -->|"ano"| DD["Dialog Zahodit rozpracovanou zakázku"]
    DD -->|"Uložit a pokračovat"| SV["stažení JSON"] --> KI
    DD -->|"Zahodit"| KI
    DD -->|"Zrušit"| BACK["zpět, beze změny"]
    H -->|"Vyzkoušet demo"| F6(["F6"])
    PH["Hlavička zakázky: Nová zakázka"] --> R2{"Neuložené změny?"}
    R2 -->|"ne"| H
    R2 -->|"ano"| DD2["Dialog Zahodit rozpracovanou zakázku"]
    DD2 -->|"Zahodit / Uložit a pokračovat (NewProjectRequested*)"| H
    RST["Restart backendu"] -.-> EXP{{"Relace vypršela: načtěte uloženou zakázku"}}
    EXP --> IMD
```

| Vstup | Výsledný krok | Plán spočítán? | Poznámka |
|---|---|---|---|
| Text | Kontrola údajů (po AI) | ne | UC-01 |
| Karta nástroje | Kontrola údajů, prázdný návrh | ne | UC-13 |
| Příklad | Kontrola údajů, štítek „Příklad“ | ne | UC-10 |
| Načtení souboru | Kontrola údajů | ne | UC-06; chyba souboru zůstává v dialogu |
| Demo | Krok Zadání, předvyplněný text | ne | UC-11 |

Návrat na Úvodní obrazovku logem v hlavičce zakázku neruší. Úvod pak nabídne „Pokračovat v zakázce“ (UC-09 A3).

---

## F5: Kalkulace

```mermaid
flowchart TD
    P["Krok Plán a cena"] --> C["Panel Kalkulace"]
    C --> MP{"Mají všechny použité tyče cenu?"}
    MP -->|"ne"| MI["Řádek materiálu: chybí cena; Celkem: neúplná kalkulace"]
    MI -->|"doplnit cenu tyče (vstup plánu)"| PE["ProposalEdited*: návrh změny"]
    PE --> GOAL{"Cíl je nejnižší cena?"}
    GOAL -->|"ano"| K["Krok Kontrola údajů, plán neaktuální"]
    GOAL -->|"ne"| QC["Potvrdit cenu, plán zůstává, kalkulace přepočtena"]
    MP -->|"ano"| OK["Materiál podle spotřebovaných tyčí"]
    C -->|"práce, náklady, přirážka, DPH (CostInputsChanged*)"| V{"Hodnota platná?"}
    V -->|"ne"| VE{{"Pole zvýrazněné, předchozí kalkulace platí"}}
    V -->|"ano"| RC["Okamžitý přepočet bez solveru"]
    RC --> C
    C -->|"Stáhnout PDF"| PA{"Plán aktuální?"}
    PA -->|"ne"| PD["Tlačítko neaktivní: nejdřív přepočítejte plán"]
    PA -->|"ano"| PR(["RenderPdf: Připravuji PDF..."])
    PR -->|"PdfRendered*"| DL["Stažení souboru"]
    PR -->|"PdfFailed*"| PF{{"Chyba u tlačítka, Zkusit znovu"}}
    PF -->|"RetryRequested*"| PR
    NP["Bez plánu"] --> MM["Materiál zadaný ručně (UC-04 A2)"]
    MM --> C
```

- Doplnění ceny tyče v Panelu Kalkulace je pohodlná zkratka, ale cena tyče je vstup plánu (R2). Vznikne proto návrh změny. Při cíli „nejnižší cena“ to znamená návrat do Kontroly údajů (R4), jinak stačí potvrdit cenu přímo v panelu („Potvrdit cenu“), vznikne nová verze a přepočítá se jen kalkulace. Plán zůstává aktuální, protože cena tyče při jiném cíli plán neovlivňuje. (Rozhodnuto při service designu: podle cíle, ne vždy přes Kontrolu údajů.)
- Prázdný stav Panelu Kalkulace bez plánu: „Kalkulace se spočítá z plánu“ s akcí „Zadat materiál ručně“ (UC-04 A2).

---

## F6: Demo režim

```mermaid
flowchart TD
    H["Úvodní obrazovka: Vyzkoušet demo"] -->|"SessionStarted* (demo)"| Z["Krok Zadání s předvyplněným textem + Pruh demo režimu"]
    Z -->|"Odeslat"| R(["Připravená odpověď routeru a extrakce (krátký simulovaný průběh)"])
    R --> K["Krok Kontrola údajů"]
    K -->|"Potvrdit a vypočítat"| S(["Skutečný výpočet"])
    S --> P["Krok Plán a cena"]
    P --> D{"Zpráva v Panelu Dialog"}
    D -->|"připravená zpráva (tlačítko)"| PR(["Připravený návrh změny"])
    PR --> K
    D -->|"volný text"| N["Odpověď: v demu umím jen připravené zprávy + tlačítka"]
    N --> D
    P -->|"Stáhnout PDF"| PDF["Skutečné PDF"]
    Z -->|"Ukončit demo (NewProjectRequested*)"| H
    P -->|"Ukončit demo"| H
```

Pruh demo režimu je viditelný na všech krocích a ve Vývojářském panelu (router „demo“). Výpočet, kalkulace a PDF nejsou simulované.

---

## F7: Vývojářský panel

```mermaid
flowchart LR
    W["Pracovní obrazovka zakázky"] -->|"ikona v hlavičce / zkratka"| D["Vývojářský panel"]
    D --> T1["Router: přepínač + poslední RoutingDecision"]
    D --> T2["AI volání: časová osa, verze promptu, trace"]
    D --> T3["Solver: vzory, dolní mez, CP-SAT"]
    D --> T4["Stav: revize, návrh, poslední události"]
    T1 -->|"RouterSwitched*"| N{"Implementace dostupná?"}
    N -->|"ano"| OK["Systémová poznámka v Panelu Dialog"]
    N -->|"ne"| X["Volba neaktivní s důvodem"]
    D -->|"zavřít / Esc"| W
```

Prázdné stavy záložek: „Zatím žádné rozhodnutí routeru“, „Zatím žádné volání AI“, „Zatím žádný výpočet“. Když je Langfuse vypnutý, záložka AI volání to uvádí a odkazy na trace chybí.

---

## F8: Řezání desek *(rozšíření)*

Tok je F1 s rozdíly jen v Kontrole údajů a v Panelu Plán:

```mermaid
flowchart TD
    A["Zadání nebo karta Řezání desek"] --> B(["Router: cutting_2d, extrakce"])
    B --> M{"Jeden materiál, tloušťka a formát?"}
    M -->|"ne"| M1["Panel Dialog: vysvětlí omezení, nabídne pokračovat s jedním materiálem"]
    M1 --> K
    M -->|"ano"| K["Kontrola údajů: díly (š × d × počet, lze otočit), formát desky, prořez, okrajový ořez"]
    K --> P{"Prořez a ořez potvrzené?"}
    P -->|"ne"| P1["Panel Dialog se doptá; hodnoty nepotvrzené"]
    P1 --> K
    P -->|"ano: Potvrdit a vypočítat"| S(["Výpočet 2D"])
    S --> R{"Výsledek"}
    R -->|"s postupem řezů"| R1["Panel Plán: Nářezový plán, desky, pořadí řezů"]
    R -->|"jen geometrie"| R2["Panel Plán: Rozložení dílů (bez postupu řezů)"]
    R -->|"díl se nevejde"| R3["Částečný: neumístěné díly s důvodem"]
```

---

## F9: Sklad v zakázce *(rozšíření)*

```mermaid
flowchart TD
    K["Kontrola údajů"] -->|"Použít sklad (ProposalEdited*)"| SK["Sekce Ze skladu: odpovídající položky"]
    SK --> E{"Shoda materiálu ve skladu?"}
    E -->|"ne"| E1["Prázdná sekce: pro tento profil nic nemáte + odkaz na Sklad"]
    E -->|"ano"| N{"Povolit nákup chybějícího?"}
    N --> C["Potvrdit a vypočítat"]
    C --> S(["Výpočet se sklad. revizí"])
    S --> R{"Výsledek"}
    R -->|"úplný"| P["Panel Plán: ze skladu / k nákupu + nákupní seznam"]
    R -->|"nákup zakázán, sklad nestačí"| PP["Částečný: neumístěné kusy, Povolit nákup a přepočítat"]
    R -->|"nic nelze umístit"| INF{{"Bez proveditelného řešení: Povolit nákup"}}
    INF -->|"ProposalEdited* + potvrzení"| S
    PP -->|"ProposalEdited* + potvrzení"| S
    P -->|"Odepsat ze skladu"| W["Dialog Zápis do skladu: odepsané položky, nové zbytky"]
    W -->|"StockChangeConfirmed*"| OK["Sklad: nová verze, záznam v historii"]
    W -->|"StockChangeRejected*"| P
    W -->|"chyba úložiště"| WE{{"Nic se nezapsalo, Zkusit znovu"}}
    WE --> W
    OK --> AG{"Tatáž verze plánu znovu?"}
    AG -->|"ano"| BL["Akce neaktivní: už odepsáno"]
    P -->|"sklad se změnil jinde"| ST["Plán neaktuální: sklad se změnil"]
```

---

## F10: Správa skladu *(rozšíření)*

```mermaid
flowchart TD
    H["Hlavička nebo karta Sklad"] --> LD(["Načítání: skeleton tabulky"])
    LD --> S["Obrazovka Sklad: tabulka položek"]
    CM["Zpráva v Panelu Dialog (UC-16 A1)"] -->|"návrh změny skladu"| D
    S --> EM{"Sklad prázdný?"}
    EM -->|"ano"| E0["Prázdný stav: co sem patří + Přidat položku"]
    EM -->|"ne"| T["Tabulka s filtrem, jen zbytky"]
    T -->|"úprava / přidání (StockChangeProposed*)"| D["Rozpracované změny zvýrazněné"]
    E0 -->|"Přidat položku"| D
    D --> V{"Položky platné?"}
    V -->|"ne"| VE{{"Chyby po polích"}}
    V -->|"ano: Uložit změny skladu"| W(["WriteStock*"])
    W -->|"StockChangeConfirmed*"| T
    W -->|"chyba úložiště"| WE{{"Hláška, změny zůstanou, Zkusit znovu"}}
    D -->|"odchod ze Skladu"| DD["Dialog Zahodit změny skladu"]
    T -->|"záložka Historie"| HX{"Existují změny?"}
    HX -->|"ano"| HI["Seznam změn: kdy, zdroj, položky"]
    HX -->|"ne"| HE["Prázdný stav: Zatím žádné změny"]
```
