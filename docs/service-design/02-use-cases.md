# Use cases

**Stav:** schváleno  
**Vychází z:** specifikace v0.3, kap. 4–8; ADR-0006; persony v [01-persony.md](01-persony.md)

Dokument zpřesňuje UC-01 až UC-08 ze specifikace a doplňuje UC-09 až UC-16. Názvy obrazovek, panelů a dialogů odpovídají slovníku v [README](README.md) a mapě obrazovek.

## Společná pravidla pro všechny případy

Tato pravidla vyplynula z rozhodnutí při service designu. Use cases na ně odkazují a neopakují je.

- **R1 Všechno je návrh.** Každá změna vstupů plánu (od AI, z formuláře nebo úpravou buňky v tabulce) mění jen rozpracovaný návrh změny (`ChangeProposal`). Zakázku mění jedině tlačítko **„Potvrdit a vypočítat“**, které vytvoří novou revizi a spustí výpočet.
- **R2 Vstupy plánu a vstupy kalkulace.** *Vstupy plánu* jsou díly, skladové délky včetně cen, parametry (prořez, ořez, minimální zbytek, časový limit, použití skladu) a cíl optimalizace. *Vstupy kalkulace* jsou práce (hodiny a sazba), další náklady, přirážka a DPH. Vstupy kalkulace se upravují přímo v panelu Kalkulace. Úprava je sama potvrzením: vytvoří revizi a kalkulace se hned přepočítá bez solveru, plán zůstává aktuální.
- **R3 Neaktuální plán** je odvozená vlastnost. Platí, když se od revize, ze které plán vznikl, změnily vstupy plánu (ceny skladových délek se počítají jen při cíli „nejnižší cena“, jinak plán neovlivňují), když čeká nepotvrzený návrh, nebo (u skladu) když se změnila revize skladu. Neaktuální plán zůstává vidět, je viditelně označený, nelze ho exportovat do PDF a nabízí výraznou akci „Přepočítat“ (případně „Zkontrolovat změny“).
- **R4 Návrh se kontroluje v kroku Kontrola údajů.** Když přijde návrh změny (i nad existujícím plánem), pracovní plocha přejde na krok Kontrola údajů se zvýrazněnými změněnými řádky a souhrnem změn. Starý plán je dostupný přes ukazatel kroků.
- **R5 Dlouhé operace** (volání AI, výpočet, PDF) ukazují průběh v konkrétním panelu a lze je zrušit. Po chybě je lze opakovat.
- **R6 Nepotvrzené hodnoty** (výchozí nastavení, odhad modelu) jsou v tabulce označené a ve výpočtu se použijí až po potvrzení celého návrhu.

## Události reduceru

Kroky scénářů uvádějí události (→ `Event`) a efekty (⇒ `Effect`) podle ADR-0006. Události a efekty, které specifikace zatím nejmenuje, jsou označené hvězdičkou (*) a shrnuté v [katalogu na konci](#katalog-událostí-a-efektů).

---

## UC-01: Vytvoření nářezového plánu tyčí

**Persony:** P1, P3 · **JTBD:** J1.1–J1.4  
**Cíl:** Převést textový seznam dílů na použitelný plán řezání.  
**Vstupní podmínky:** Je otevřená nová prázdná zakázka (UC-09, UC-15).  
**Výstupní podmínky (úspěch):** Existuje potvrzená revize zakázky a k ní aktuální plán se štítkem stavu řešení. Každý kus je umístěný právě jednou nebo výslovně označený jako neumístěný.

**Hlavní scénář**

1. Uživatel napíše zadání do pole v kroku Zadání, např. „deset jeklů 40×40 po 2 m a pět příček po 1,5 m, kupuju šestimetrové tyče po 420 Kč“, a odešle ho. → `MessageSent`
2. Panel Dialog zobrazí zprávu a stav „Rozpoznávám úlohu…“. ⇒ `CallRouter`
3. Router vrátí `cutting_1d` a záměr „nová zakázka“. → `RoutingDecided`* ⇒ `CallExtractor` (režim nová zakázka)
4. Panel Dialog ukáže „Připravuji údaje ke kontrole…“ s možností zrušit.
5. Model vrátí strukturovaná data v milimetrech, která projdou validací schématu. → `ProposalReceived`
6. Pracovní plocha přejde na krok **Kontrola údajů**. Ukáže tabulku dílů, tabulku skladových délek s cenami, parametry (prořez, zarovnávací ořez, minimální využitelný zbytek) a cíl optimalizace. Hodnoty z výchozího nastavení nebo odhadnuté modelem jsou označené jako nepotvrzené (R6).
7. Panel Dialog shrne, co aplikace rozpoznala, a upozorní na nepotvrzené hodnoty.
8. Uživatel opraví, co nesedí (úprava buňky, přidání nebo smazání řádku). → `ProposalEdited`*
9. Uživatel zvolí „Potvrdit a vypočítat“. → `ProposalConfirmed` (nová revize) ⇒ `RunSolver` → `SolveRequested`
10. Pracovní plocha přejde na krok **Plán a cena**. Panel Plán ukáže průběh výpočtu a možnost zrušit.
11. Solver vrátí výsledek. → `SolveFinished`
12. Panel Plán zobrazí měřítkový plán tyčí s pořadím dílů na tyči, rozpis dílů, štítek stavu řešení a metriky (spotřebované tyče, délka dílů, odpad, využitelné zbytky, výtěžnost). Panel Kalkulace zobrazí materiálové náklady podle spotřebovaných tyčí (UC-04).

**Alternativy**

- **A1 Přímý výběr nástroje.** Uživatel na úvodní obrazovce nebo v kroku Zadání zvolí kartu „Řezání tyčí“. → `ToolSelected` Router i extrakce se přeskočí a pokračuje se ručním zadáním (UC-13).
- **A2 Chybějící skladová délka.** Extrakce skladovou délku nenašla. Tabulka skladových délek nabídne výchozí 6000 mm jako nepotvrzenou hodnotu a Panel Dialog se zeptá: „Jaké délky tyčí nakupujete?“ Uživatel délku doplní v tabulce nebo odpoví zprávou (→ UC-03).
- **A3 Cíl „nejnižší cena“ bez kompletních cen.** Výchozí cíl je „nejméně materiálu“ (nepotvrzený). Pokud uživatel zvolí „nejnižší cena“ a některá cena chybí, tlačítko „Potvrdit a vypočítat“ je neaktivní a pole bez ceny jsou zvýrazněná s nabídkou „doplnit ceny“ nebo „zvolit jiný cíl“.
- **A4 Příliš dlouhý díl.** Díl delší než nejdelší skladová délka (po odečtení ořezu) je v kontrolní tabulce označený varováním. Výpočet lze spustit, ale výsledek má stav „částečný“ a samostatný seznam neumístěných kusů. Nepůsobí jako splněná zakázka.
- **A5 Nejlepší nalezený plán.** Solver neprokáže optimum v časovém limitu. Štítek „Nejlepší nalezený“ s rozdílem od dolní meze („nejvýš o 1 tyč víc, než je teoretické minimum“).
- **A6 Uživatel zruší výpočet.** → `OperationCancelled`* Žádný nový výsledek nevznikne, Panel Plán ukáže „Výpočet zrušen“ a akci „Přepočítat“. Potvrzená revize zůstává.
- **A7 Zadání s cenou za metr.** Model cenu za tyč nepřepočítává. Cena se uloží jako nepotvrzená s poznámkou „cena za metr, ověřte cenu za tyč“. Převod spočítá kód, ne model.

**Chybové větve**

- **E1 Validace selže** (záporná délka, chybějící povinné pole). Pole jsou zvýrazněná s konkrétní hláškou, „Potvrdit a vypočítat“ je neaktivní a seznam chyb je nad tabulkou s odkazy na pole.
- **E2 Selhání AI** → `AiFailed`. Viz UC-07.
- **E3 Nejasné nebo nepodporované zadání.** Viz UC-05.
- **E4 Solver selže** (neočekávaná chyba) → `SolveFailed`*. Panel Plán ukáže lidskou hlášku a akci „Zkusit znovu“, ve vývojářském panelu je detail. Revize zůstává potvrzená.

---

## UC-02: Rozmístění dílů na desky *(rozšíření)*

**Persony:** P2 · **JTBD:** J2.1–J2.3  
**Cíl:** Získat prostorově platný plán pro pravoúhlé díly.  
**Vstupní podmínky:** Schopnost `cutting_2d` je implementovaná a zapnutá v registru. Jinak se karta „Řezání desek“ ani router tuto volbu nenabízí.  
**Výstupní podmínky (úspěch):** Aktuální plán desek, v němž díly nepřesahují použitelnou oblast, nepřekrývají se, respektují prořez a povolenou orientaci a mají deklarovaný postup řezů.

**Hlavní scénář**

1. Uživatel napíše zadání, např. „police z lamina 18 mm: 4× 800×300, 2× 1200×300, deska 2800×2070, dekor po délce“, nebo zvolí kartu „Řezání desek“. → `MessageSent` / `ToolSelected`
2. Router vrátí `cutting_2d`. ⇒ `CallExtractor` → `ProposalReceived`
3. Krok Kontrola údajů ukáže tabulku dílů (šířka, délka, počet, **lze otočit**), formát desky s cenou za kus, materiál a tloušťku jako informaci a parametry (prořez, okrajový ořez). Prořez a okrajový ořez bez výslovné hodnoty jsou nepotvrzené a Panel Dialog se na ně doptá.
4. Uživatel doplní hodnoty, u dílů s dekorem zakáže otáčení (u „dekor po délce“ je zakázání předvyplněné jako nepotvrzené) a potvrdí. → `ProposalEdited`*, `ProposalConfirmed` ⇒ `RunSolver`
5. Panel Plán zobrazí desky jako měřítkový obrázek: polohy dílů, otočené díly označené, číslované pořadí gilotinových řezů a ořez okrajů. Metriky jsou počet desek, využití plochy a odpad. Štítek je zpravidla „Nejlepší nalezený“, „Optimální“ jen při dosažení dolní meze z plochy.

**Alternativy**

- **A1 Více materiálů v zadání** („lamino a překližka“). Jedna úloha má jeden materiál, tloušťku a formát. Panel Dialog vysvětlí omezení a nabídne „Pokračovat s laminem“; druhý materiál lze zadat jako novou zakázku (UC-15).
- **A2 Díl se nevejde** (ani otočený, nebo otočení je zakázané). Stav „částečný“ se seznamem neumístěných dílů a důvodem.
- **A3 Rozmístění bez ověřeného postupu řezů.** Pokud solver vrátí jen geometrii, výsledek se jmenuje „Rozložení dílů“ místo „Nářezový plán“ a PDF nese stejný název.
- **A4 Nepravidelný tvar** („kruhová deska stolu“). Router nebo validace vrátí `unsupported` pro daný díl. Viz UC-05.

**Chybové větve:** jako UC-01 (E1–E4).

---

## UC-03: Navazující změna zakázky

**Persony:** P1, P3 · **JTBD:** J1.5  
**Cíl:** Upravit zakázku větou bez opakování všech údajů.  
**Vstupní podmínky:** Existuje potvrzená zakázka (s plánem nebo bez něj).  
**Výstupní podmínky (úspěch):** Nová revize obsahuje jen zamýšlené změny, ostatní hodnoty jsou zachované a nový plán i kalkulace jsou aktuální. Změna je dohledatelná v historii revizí.

**Hlavní scénář**

1. Nad plánem uživatel napíše do Panelu Dialog: „Přidej dvě příčky po 850 mm, ostatní nech.“ → `MessageSent`
2. ⇒ `CallRouter` → `RoutingDecided`* (záměr „úprava zakázky“) ⇒ `CallExtractor` (režim změna, dostane aktuální potvrzenou zakázku)
3. Model vrátí návrh změny proti aktuální revizi. → `ProposalReceived`
4. Pracovní plocha přejde na krok Kontrola údajů (R4). Přidané řádky jsou zvýrazněné jako nové, změněné hodnoty ukazují původní hodnotu přeškrtnutou a nad tabulkou je **souhrn změn** („+ 2× příčka 850 mm“).
5. Plán v kroku Plán a cena je od této chvíle neaktuální (R3).
6. Uživatel změnu zkontroluje a zvolí „Potvrdit a vypočítat“. → `ProposalConfirmed` ⇒ `RunSolver` → `SolveFinished`
7. Krok Plán a cena ukáže nový plán. Kalkulace se přepočítá podle nově spotřebovaných tyčí. Panel Dialog potvrdí „Změna uložena jako verze 3, plán přepočítán“.

**Alternativy**

- **A1 Nejednoznačný odkaz** („Prodluž to o deset“). Model vrátí otázku místo návrhu. → `ClarificationReceived`* Panel Dialog zobrazí jednu konkrétní otázku („Kterou položku a o kolik — 10 mm, nebo 10 cm?“), případně s volbami jako tlačítky. Zakázka ani návrh se nemění.
- **A2 Zahození návrhu.** Uživatel zvolí „Zahodit změny“. → `ProposalRejected` Pracovní plocha se vrátí na předchozí krok a plán je opět aktuální.
- **A3 Ruční doladění návrhu.** Uživatel v tabulce upraví navržené hodnoty před potvrzením. → `ProposalEdited`*
- **A4 Další zpráva během čekajícího návrhu.** Nová zpráva upraví rozpracovaný návrh, nevytvoří druhý. Souhrn změn se aktualizuje a ukazuje rozdíl proti poslední potvrzené revizi.
- **A5 Změna jen vstupů kalkulace** („sazba 450 Kč na hodinu“). Router rozpozná `cost_estimate`. Model navrhne hodnotu do panelu Kalkulace, kde je zvýrazněná jako nepotvrzená s tlačítkem „Použít“. Po potvrzení → `CostInputsChanged`* (R2). Plán se nepřepočítává.
- **A6 Změna bez plánu.** Je-li zakázka potvrzená, ale plán dosud nevznikl (např. po importu), postup je stejný. Krok 5 odpadá.

**Chybové větve**

- **E1 Návrh neprojde validací.** Návrh se zobrazí s chybami po polích a poslední validní revize zůstává beze změny. „Potvrdit a vypočítat“ je neaktivní, dokud uživatel chyby neopraví.
- **E2 Návrh by smazal všechny díly** nebo jinak zásadně změnil zakázku. Souhrn změn to zvýrazní varováním. Potvrzení je stále na uživateli.
- **E3 Selhání AI.** Viz UC-07. Rozpracovaný návrh i potvrzená zakázka zůstávají.

---

## UC-04: Orientační kalkulace

**Persony:** P3 · **JTBD:** J3.1–J3.3  
**Cíl:** Vyčíslit náklady zakázky z plánu a vlastních cen.  
**Vstupní podmínky:** Existuje plán, nebo uživatel zadá ručně položky materiálu (viz A2).  
**Výstupní podmínky (úspěch):** Kalkulace s rozpadem materiál / práce / další náklady / přirážka / DPH, se seznamem cenových předpokladů a chybějících položek. Každá částka je odvoditelná ze zobrazených vstupů.

**Hlavní scénář**

1. V kroku Plán a cena Panel Kalkulace ukáže materiál podle spotřebovaných tyčí. Cena za tyč pochází ze vstupů plánu.
2. Uživatel doplní hodiny práce, hodinovou sazbu a další náklady (položka a částka). → `CostInputsChanged`*
3. Volitelně zadá přirážku k nákladům v % a sazbu DPH. → `CostInputsChanged`*
4. Kalkulace se po každé změně přepočítá do 100 ms bez solveru (R2) a ukáže řádky, mezisoučty, přirážku, DPH a celkem.
5. Pod kalkulací jsou cenové předpoklady („cena tyče 6 m: 420 Kč, zadáno uživatelem“, „přirážka se počítá z nákladů“).
6. Uživatel zvolí „Stáhnout PDF“. ⇒ `RenderPdf` → `PdfRendered`* PDF obsahuje plán, rozpis a kalkulaci a je označené jako orientační kalkulace.

**Alternativy**

- **A1 Chybí cena tyče.** Řádek materiálu ukazuje „chybí cena“, nikdy 0 Kč. Celkem se označí „neúplná kalkulace“ a je vyjmenováno, co chybí. Cenu tyče lze doplnit přímo v Panelu Kalkulace. Protože je to vstup plánu, vznikne tím návrh změny (R1) a plán se při cíli „nejnižší cena“ stane neaktuálním. Při jiném cíli se po potvrzení jen přepočítá kalkulace.
- **A2 Kalkulace bez plánu** (záměr `cost_estimate` bez existujícího plánu). Panel Dialog nabídne „Nejdřív vytvořit plán“ (→ UC-01), nebo „Zadat materiál ručně“: Panel Kalkulace pak má tabulku položek materiálu (položka, počet, cena za kus).
- **A3 Při zapnutém skladu** se materiál ze skladu oceňuje evidovanou cenou. Přepínač „Nezapočítávat materiál ze skladu“ se uvede mezi předpoklady (UC-08).

**Chybové větve**

- **E1 Neplatná hodnota** (záporné hodiny, text místo čísla). Pole je zvýrazněné, předchozí platná kalkulace zůstává a revize nevznikne.
- **E2 PDF selže** → `PdfFailed`*. Hláška u tlačítka a akce „Zkusit znovu“. Zakázku lze stále uložit jako JSON.
- **E3 Plán je neaktuální.** „Stáhnout PDF“ je neaktivní s vysvětlením „Nejdřív přepočítejte plán“.

---

## UC-05: Nejasné nebo nepodporované zadání

**Persony:** P1, S3 · **JTBD:** J1.1, JS3.2  
**Cíl:** Dovést uživatele k podporované úloze, aniž by se spustil nesouvisející výpočet.  
**Výstupní podmínky (úspěch):** Uživatel upřesnil zadání nebo vybral nástroj. Žádný solver se nespustil s nesmyslnými daty a nic nesliboval nepodporované řešení.

**Hlavní scénář (nejasné)**

1. Uživatel napíše „Chci vyrobit skříň.“ → `MessageSent` ⇒ `CallRouter`
2. Router vrátí `unclear`, nebo nízkou confidence pod nastaveným prahem. → `RoutingDecided`*
3. Panel Dialog zformuluje jednu konkrétní otázku: „Potřebujete nařezat desky na díly skříně, nebo tyče na rám?“ Pod ní jsou karty dostupných nástrojů jako rychlá volba.
4. Uživatel odpoví zprávou (→ znovu router s kontextem) nebo vybere kartu (→ `ToolSelected`). Dál pokračuje UC-01 nebo UC-02.

**Alternativy**

- **A1 Nepodporované** („Naskládej bedny do dodávky“). Router vrátí `unsupported`. Panel Dialog vysvětlí, co aplikace umí („Umím plánovat řezání tyčí a spočítat cenu“), nabídne karty dostupných nástrojů a nic nepočítá.
- **A2 Rozšíření není implementované.** Zadání na desky, když `cutting_2d` chybí, se chová jako `unsupported`. Hláška nezmiňuje nedokončenou funkci jako „brzy dostupnou“.
- **A3 Rozporné odpovědi routeru** (typ úlohy vs. záměr). Aplikace se doptá stejně jako u `unclear`.

**Chybové větve:** Selhání routeru → UC-07 (nabídne ruční výběr nástroje).

---

## UC-06: Uložení a pokračování

**Persony:** P3 · **JTBD:** J3.6  
**Cíl:** Uložit zakázku do souboru a později v ní pokračovat.  
**Výstupní podmínky (úspěch):** Načtená zakázka má stejné vstupy plánu, cíl optimalizace, ceny a vstupy kalkulace jako uložená. Import nevolal žádné API.

**Hlavní scénář — uložení**

1. V hlavičce zakázky uživatel zvolí „Uložit zakázku“. Stáhne se JSON pojmenovaný podle názvu zakázky (`plot-zahrada.decision.json`).
2. Soubor obsahuje verzi formátu, potvrzenou revizi a vstupy kalkulace. Neobsahuje API klíče. Historie dialogu je volitelná.

**Hlavní scénář — načtení**

1. Na úvodní obrazovce nebo v hlavičce zakázky uživatel zvolí „Načíst zakázku“ a vybere soubor (nebo ho přetáhne). → `ProjectImported`
2. Jádro ověří verzi formátu a strukturu.
3. Pracovní plocha ukáže krok Kontrola údajů s obnovenými daty. Plán se nevypočítá automaticky. Panel Dialog řekne „Zakázka načtena. Zkontrolujte údaje a spusťte výpočet.“
4. Uživatel zvolí „Potvrdit a vypočítat“ (→ UC-01, krok 9).

**Alternativy**

- **A1 Rozpracovaná zakázka při načítání.** Pokud má aktuální zakázka neuložené změny, zobrazí se Dialog Zahodit rozpracovanou zakázku (viz UC-15).
- **A2 Uložení s nepotvrzeným návrhem.** Ukládá se jen potvrzená revize. Hlavička na to upozorní („Neuložené změny v návrhu nebudou součástí souboru“).
- **A3 Starší verze formátu.** Pokud je převod možný, provede se a zakázka se načte. Panel Dialog to oznámí.

**Chybové větve**

- **E1 Neplatný soubor** (není JSON, neznámá verze, chybí povinná pole). Hláška v Dialogu Načíst zakázku, např. „Soubor není zakázka DecisionEngine“ nebo „chybí skladové délky“. Aktuální zakázka zůstává beze změny.
- **E2 Částečně neplatná data** (záporná délka). Načte se jako návrh se zvýrazněnými chybami (R1), ne jako potvrzená zakázka.

---

## UC-07: Práce při výpadku AI

**Persony:** P1, S1 · **JTBD:** J1.1, JS1.2  
**Cíl:** Dokončit výpočet a export i bez vzdálené AI.  
**Výstupní podmínky (úspěch):** Rozepsaný text i platná data jsou zachované a uživatel dokončí zakázku lokálním routerem nebo ručně.

**Hlavní scénář**

1. Volání routeru nebo extrakce selže. → `AiFailed` (druh: připojení / vyčerpaný limit / neplatná odpověď)
2. Panel Dialog ukáže chybovou zprávu podle druhu chyby:
   - *připojení:* „Nepodařilo se spojit se službou AI.“ → Zkusit znovu / Ruční zadání
   - *limit:* „Vyčerpaný limit služby AI, zkuste to za 2 minuty.“ → Ruční zadání / (pokud je dostupný) Použít lokální rozpoznávání
   - *neplatná odpověď:* „AI vrátila nepoužitelná data.“ → Zkusit znovu / Ruční zadání
3. Text zprávy zůstane v poli, takže ho uživatel nemusí psát znovu.
4. Uživatel zvolí jednu z akcí: → `RetryRequested`* / `ToolSelected` (ruční zadání, UC-13) / `RouterSwitched`* (Layo).
5. Výpočet, kalkulace a export fungují bez AI.

**Alternativy**

- **A1 Opakované selhání.** Opakování je omezené (např. 2 automatické pokusy na adaptéru). Pak už se nabízí jen ruční cesta.
- **A2 Langfuse nedostupný.** Uživatel nic nevidí. Prompty se vezmou ze záložní kopie a ve vývojářském panelu je poznámka „trasování vypnuto“.
- **A3 Chybí klíč Groq od startu.** Viz UC-09 A2: AI funkce jsou od začátku viditelně nedostupné, ruční zadání a demo fungují.

---

## UC-08: Využití skladu a zbytků *(rozšíření)*

**Persony:** P3 · **JTBD:** J3.4, J3.5  
**Cíl:** Spotřebovat nejdřív materiál ze skladu a dokoupit jen chybějící.  
**Vstupní podmínky:** Rozšíření sklad je implementované. Ve skladu jsou položky (UC-16).  
**Výstupní podmínky (úspěch):** Plán nepoužije víc kusů, než je na skladě. Rozlišuje tyče „ze skladu“ a „k nákupu“. Sklad se mění až po výslovném potvrzení a každá změna je dohledatelná.

**Hlavní scénář**

1. Uživatel v zadání napíše „použij nejdřív zbytky ze skladu“, nebo v kroku Kontrola údajů zapne přepínač „Použít sklad“. → `ProposalEdited`*
2. Kontrola údajů ukáže sekci **Ze skladu**: odpovídající položky podle identifikátoru materiálu/profilu (délka, počet k dispozici, cena, příznak zbytku) a přepínač „Povolit nákup chybějícího materiálu“ (výchozí zapnuto).
3. Uživatel potvrdí. → `ProposalConfirmed` ⇒ `RunSolver` (s revizí skladu)
4. Panel Plán barevně i textem rozliší tyče ze skladu a tyče k nákupu. Metriky ukazují „ze skladu: 3 tyče (2 zbytky)“ a „k nákupu: 4× 6000 mm“. Nákupní seznam je samostatný blok.
5. Panel Kalkulace ocení skladový materiál evidovanou cenou. Lze zvolit „Nezapočítávat materiál ze skladu“ (předpoklad se vypíše).
6. Po výrobě uživatel zvolí „Odepsat ze skladu“. Otevře se Dialog Zápis do skladu se seznamem: odepsané položky a nové využitelné zbytky (délka, počet), které lze upravit nebo odškrtnout. → `StockChangeProposed`*
7. Uživatel potvrdí. → `StockChangeConfirmed`* Sklad má novou revizi a záznam `StockChange` (kdy, zakázka, revize, položky). Panel Dialog to potvrdí.

**Alternativy**

- **A1 Nákup zakázán a sklad nestačí.** Výsledek je „částečný“, se seznamem neumístěných kusů a akcí „Povolit nákup a přepočítat“.
- **A2 Materiál zakázky nemá ve skladu shodu.** Sekce Ze skladu je prázdná s hláškou „Pro profil jekl 40×40×2 nemáte na skladě nic“ a odkazem na Sklad.
- **A3 Sklad se změnil po výpočtu** (např. úpravou na obrazovce Sklad). Plán je neaktuální (R3) a ukazuje důvod „Sklad se od výpočtu změnil“.
- **A4 Uživatel zápis zruší.** → `StockChangeRejected`* Sklad zůstává beze změny a akci lze zopakovat.
- **A5 Opakovaný zápis z téže revize.** Je zablokovaný s hláškou „Tato verze plánu už byla ze skladu odepsána“.

**Chybové větve**

- **E1 Zápis do úložiště selže.** Hláška a akce „Zkusit znovu“. Stav skladu se nezmění částečně (zápis je atomický).

---

## UC-09: První spuštění a úvodní obrazovka

**Persony:** S3, S1 · **JTBD:** JS3.1, JS1.1  
**Cíl:** Na první pohled pochopit, co aplikace dělá a čím začít.  
**Vstupní podmínky:** Aplikace je spuštěná jedním příkazem a otevřená v prohlížeči.  
**Výstupní podmínky (úspěch):** Uživatel začal zakázku (textem, výběrem nástroje, příkladem, demem nebo načtením).

**Hlavní scénář**

1. Uživatel otevře aplikaci. → `SessionStarted`*
2. Úvodní obrazovka ukáže název, popis „Ze zadání k nářezovému plánu a ceně zakázky“, velké textové pole se střídajícími se ukázkami zadání, karty nástrojů („Řezání tyčí“, „Kalkulace“, rozšíření jen pokud existují) a akce „Načíst zakázku“, „Otevřít příklad“ a „Vyzkoušet demo“.
3. Uživatel napíše zadání a odešle ho. Aplikace přejde na pracovní obrazovku zakázky a pokračuje UC-01 od kroku 2.

**Alternativy**

- **A1 Klik na kartu nástroje** → pracovní obrazovka, krok Zadání s předvoleným nástrojem (UC-13 nebo UC-04 A2).
- **A2 Chybí klíč Groq.** Textové pole je dostupné, jen pokud je k dispozici lokální router a extrakce. Jinak je pole neaktivní s vysvětlením „AI není nastavená (chybí klíč). Můžete zadat údaje ručně nebo vyzkoušet demo.“ Odkaz vede na postup v README.
- **A3 Návrat na úvod** z pracovní obrazovky (logo). Rozpracovaná zakázka v relaci zůstává a úvod nabídne „Pokračovat v zakázce“.

**Chybové větve**

- **E1 Backend neběží.** Celostránková chyba „Aplikace se nemůže spojit se svým serverem. Spusťte `uv run decision-engine`.“ a tlačítko „Zkusit znovu“.

---

## UC-10: Otevření připraveného příkladu

**Persony:** S1, S3 · **JTBD:** JS1.1  
**Cíl:** Jedním klikem vidět vyplněnou zakázku bez psaní zadání.  
**Výstupní podmínky (úspěch):** Zakázka z příkladu je načtená v kroku Kontrola údajů a označená jako příklad.

**Hlavní scénář**

1. Uživatel na úvodní obrazovce zvolí „Otevřít příklad“. Zobrazí se Dialog Příklady se seznamem: „Plot z jeklů“, „Regál z L profilů“, „Rám s více délkami tyčí“, u rozšíření i „Police z lamina“ a „Plot se zbytky ze skladu“. Každý příklad má jednu větu popisu.
2. Uživatel vybere příklad. → `ExampleOpened`* ⇒ `LoadExample`* → `ProjectImported`
3. Pracovní obrazovka ukáže krok Kontrola údajů s daty příkladu. Panel Dialog obsahuje původní textové zadání příkladu jako první zprávu a hlavička ukazuje štítek „Příklad“.
4. Uživatel pokračuje jako v UC-06 krok 4.

**Alternativy**

- **A1 Rozpracovaná zakázka** → Dialog Zahodit rozpracovanou zakázku (UC-15).
- **A2 Příklad k rozšíření, které není implementováno**, se v seznamu nezobrazí.

**Poznámka:** Příklad je obyčejná zakázka v JSON. Nepoužívá AI a funguje offline. Text zadání v něm je „jak by ho uživatel napsal“, extrakci ale nesimuluje. Živou extrakci ukazuje UC-01, připravenou extrakci demo (UC-11).

---

## UC-11: Demo režim

**Persony:** S1 · **JTBD:** JS1.2  
**Cíl:** Projít celý hlavní tok včetně „AI“ kroků bez sítě a klíčů, s poctivým označením.  
**Výstupní podmínky (úspěch):** Uživatel prošel zadání → kontrola → plán → úprava dialogem → přepočet → export a po celou dobu viděl, že jde o připravená data.

**Hlavní scénář**

1. Uživatel na úvodní obrazovce zvolí „Vyzkoušet demo“. → `SessionStarted`* (režim demo)
2. Celou aplikaci provází **Pruh demo režimu**: „Demo: odpovědi AI jsou předem připravené, výpočty jsou skutečné.“ s akcí „Ukončit demo“.
3. Krok Zadání je předvyplněný textem demo zakázky. Uživatel ho odešle. Router a extrakce použijí připravené odpovědi (falešné adaptéry) se simulovaným krátkým průběhem.
4. Kontrola údajů, výpočet, kalkulace a PDF běží skutečně.
5. Panel Dialog nabídne připravené navazující zprávy jako tlačítka („Přidej dvě příčky po 850 mm“). Odeslání vytvoří připravený návrh změny (→ UC-03).
6. Volný text mimo připravené zprávy dostane odpověď „V demu umím jen připravené zprávy“ s nabídkou tlačítek.

**Alternativy**

- **A1 Layo je k dispozici.** Demo může místo připraveného routeru použít lokální Layo. Pruh to uvádí („rozpoznání úlohy: lokální model“).
- **A2 Ukončení dema** → `NewProjectRequested` Návrat na úvodní obrazovku, demo data se zahodí.

**Poznámka:** Demo se vždy označuje. Připravené odpovědi se nikdy nevydávají za živé volání modelu (spec. kap. 12).

---

## UC-12: Vývojářský panel a přepnutí routeru

**Persony:** S2, S1 · **JTBD:** JS2.1–JS2.4, JS1.3  
**Cíl:** Vidět interní rozhodnutí a diagnostiku a za běhu přepnout implementaci routeru.  
**Výstupní podmínky (úspěch):** Diagnostika je vidět bez tajných údajů a další volání použije zvolený router.

**Hlavní scénář**

1. Uživatel otevře Vývojářský panel ikonou v hlavičce nebo klávesovou zkratkou. Panel se vysune vpravo a hlavní tok zůstává použitelný.
2. Panel má záložky:
   - **Router:** aktuální implementace, přepínač Jev / Layo / LLM / Ruční (jen dostupné) a poslední `RoutingDecision` (volba, pravděpodobnosti všech možností jako pruhy, confidence, práh, model, důvod záložního postupu).
   - **AI volání:** časová osa volání (role, model, verze promptu, latence, tokeny, stav validace, odkaz na trace v Langfuse, pokud je zapnutý).
   - **Solver:** počet vzorů, dolní mez, stav CP-SAT, čas a časový limit.
   - **Stav:** číslo revize zakázky a skladu, čekající návrh, posledních N událostí reduceru.
3. Uživatel přepne router na Layo. → `RouterSwitched`* Panel Dialog vloží systémovou poznámku „Rozpoznávání úlohy: lokální model“ a další zpráva použije Layo.

**Alternativy**

- **A1 Implementace nedostupná** (chybí klíč TypeSafe, Layo není nainstalované). Volba je neaktivní s důvodem.
- **A2 Langfuse vypnutý.** Odkazy na trace chybí a v záložce AI volání je poznámka „trasování vypnuto, prompty ze záložní kopie“.

**Pravidla:** Panel nikdy neukazuje klíče. Hlavní UI interní pojmy nepoužívá, panel ano.

---

## UC-13: Ruční zadání formulářem

**Persony:** P1, P2, S3 · **JTBD:** J1.2, J2.1  
**Cíl:** Vytvořit zakázku bez AI.  
**Vstupní podmínky:** Žádné. Funguje bez sítě a klíčů.  
**Výstupní podmínky (úspěch):** Stejné jako UC-01. Výsledek se neliší od cesty přes AI.

**Hlavní scénář**

1. Uživatel zvolí kartu nástroje („Řezání tyčí“) nebo v kroku Zadání odkaz „Zadat ručně“. → `ToolSelected`
2. Pracovní plocha přejde rovnou na krok Kontrola údajů s prázdnými tabulkami. Jde o prázdný návrh (R1). Výchozí parametry jsou předvyplněné jako nepotvrzené a tabulka dílů má jeden prázdný řádek s fokusem.
3. Uživatel vyplní díly klávesnicí: Tab mezi buňkami, Enter přidá řádek, jednotky lze psát s hodnotou („1,5 m“ se převede na 1500 mm a převod se ukáže). → `ProposalEdited`*
4. Vyplní skladové délky a ceny, zkontroluje parametry a cíl a zvolí „Potvrdit a vypočítat“. Dál pokračuje UC-01 od kroku 9.

**Alternativy**

- **A1 Vložení ze schránky.** Vložení více řádků z tabulkového procesoru (název, délka, počet) vytvoří řádky. Nejasné jednotky se zeptají („Jsou délky v mm, nebo cm?“).
- **A2 Kombinace s dialogem.** I v ručním režimu lze psát do Panelu Dialog („přidej 3 sloupky po 2,2 m“). Výsledek je úprava téhož návrhu (UC-03 A4).

- **A3 Úprava potvrzené zakázky.** Ve výsledku nebo v kroku Kontrola údajů uživatel zvolí „Upravit údaje“. → `EditRequested` Vznikne návrh se stejnými hodnotami (nic není nepotvrzené) a dál se pokračuje krokem 3; plán je do potvrzení neaktuální (R3).

**Chybové větve:** Validace po polích (UC-01 E1). Prázdný ruční formulář chyby nehlásí, dokud uživatel nezačne vyplňovat; tlačítko „Potvrdit a vypočítat“ je do té doby neaktivní s důvodem.

---

## UC-14: Dotaz k výsledku

**Persony:** P1, P3 · **JTBD:** J1.3, J3.1  
**Cíl:** Dostat vysvětlení výsledku bez změny zakázky.  
**Vstupní podmínky:** Existuje plán.  
**Výstupní podmínky (úspěch):** Odpověď se opírá jen o dodané metriky. Zakázka ani návrh se nezměnily.

**Hlavní scénář**

1. Uživatel napíše „Proč potřebuju 5 tyčí, když dílů je jen 23 metrů?“ → `MessageSent` ⇒ `CallRouter` → `RoutingDecided`* (záměr „dotaz k výsledku“)
2. ⇒ `CallExplainer`* (dostane plán, metriky a štítek stavu řešení) → `ExplanationReceived`*
3. Panel Dialog zobrazí odpověď. Čísla v odpovědi pocházejí z metrik a jsou zobrazená jako odkazy, které zvýrazní příslušný údaj v Panelu Plán (např. „odpad 1 240 mm“).

**Alternativy**

- **A1 Dotaz vyžaduje nový výpočet** („A kolik by to bylo s dvanáctimetrovými tyčemi?“). Odpověď nevymýšlí číslo. Nabídne „Vyzkoušet jako změnu zakázky“ a otevře návrh změny (UC-03).
- **A2 Plán je neaktuální.** Odpověď na to upozorní („Vysvětlení se týká předchozí verze plánu“).
- **A3 Žádný plán neexistuje.** Panel Dialog odpoví, že zatím není co vysvětlit, a nabídne další krok podle stavu zakázky.

**Chybové větve:** Selhání AI → UC-07. Ruční alternativa zde není potřeba, výsledek je dál použitelný.

---

## UC-15: Nová zakázka

**Persony:** P1, P3 · **JTBD:** J1.1, J3.6  
**Cíl:** Začít novou zakázku s prázdným kontextem a neztratit omylem rozpracovanou práci.  
**Výstupní podmínky (úspěch):** Nová prázdná zakázka, prázdný Panel Dialog a prázdná historie revizí.

**Hlavní scénář**

1. Uživatel v hlavičce zakázky zvolí „Nová zakázka“.
2. Pokud aktuální zakázka nemá neuložené změny, → `NewProjectRequested` a aplikace přejde na úvodní obrazovku (nebo krok Zadání prázdné zakázky).
3. Pokud neuložené změny má, zobrazí se Dialog Zahodit rozpracovanou zakázku: „Zakázka ‚Plot zahrada‘ má neuložené změny.“ → **Uložit a pokračovat** / **Zahodit** / **Zrušit**.

**Alternativy**

- **A1 Nová zakázka zprávou** („teď něco úplně jiného: regál…“). Router rozpozná záměr „nová zakázka“ a Panel Dialog se zeptá „Začít novou zakázku? Aktuální nebude uložena.“ s tlačítky. Bez potvrzení se kontext nemaže.

**Poznámka:** „Neuložené změny“ znamená, že potvrzená revize nebo vstupy kalkulace se liší od naposledy uloženého či načteného souboru, nebo že existuje rozpracovaný návrh. Relace drží jednu zakázku. Víc zakázek najednou není v rozsahu.

---

## UC-16: Správa skladu *(rozšíření)*

**Persony:** P3 · **JTBD:** J3.4, J3.5  
**Cíl:** Udržovat seznam materiálu a zbytků, které dílna má.  
**Vstupní podmínky:** Rozšíření sklad je implementované.  
**Výstupní podmínky (úspěch):** Sklad odpovídá skutečnosti. Každá změna má záznam a novou revizi skladu.

**Hlavní scénář**

1. Uživatel otevře obrazovku **Sklad** z hlavičky nebo z karty „Sklad“ na úvodní obrazovce.
2. Obrazovka ukáže tabulku položek: materiál/profil (výběr z identifikátorů), délka, počet, cena za kus, příznak „zbytek“ a původ (ruční / ze zakázky X). Nad tabulkou je filtr podle materiálu a přepínač „jen zbytky“.
3. Uživatel přidá nebo upraví položku. Změny se sbírají jako rozpracovaná úprava a řádky jsou zvýrazněné. → `StockChangeProposed`*
4. Zvolí „Uložit změny skladu“. → `StockChangeConfirmed`* Vznikne nová revize skladu a záznam `StockChange` (zdroj „ruční úprava“).
5. Záložka **Historie** ukazuje seznam změn (kdy, zdroj, položky).

**Alternativy**

- **A1 Úprava zprávou** („Přidej na sklad 3 zbytky jeklu 40×40 po 1,2 m“). Model vytvoří návrh změny skladu, který se zobrazí na obrazovce Sklad ke kontrole. Bez potvrzení se sklad nemění.
- **A2 Odchod s neuloženými změnami** → Dialog Zahodit změny skladu.
- **A3 Změna skladu při otevřené zakázce s plánem** zneaktuální plán, pokud používal sklad (UC-08 A3).

**Chybové větve**

- **E1 Neplatná položka** (nulová délka, neznámý materiál). Validace po polích.
- **E2 Úložiště nedostupné** (SQLite soubor zamčený). Hláška, změny zůstanou rozpracované a lze opakovat.

---

## Katalog událostí a efektů

Události ze specifikace (kap. 7) jsou bez hvězdičky. Ostatní jsou návrh tohoto dokumentu. Finální názvy určí implementace reduceru v M1–M3 a ADR-0006 se doplní jen tehdy, pokud se změní princip.

| Událost | Kdo ji vyvolá | Popis | UC |
|---|---|---|---|
| `SessionStarted`* | frontend | Nová relace, režim běžný / demo | 09, 11 |
| `MessageSent` | uživatel | Zpráva v Panelu Dialog nebo zadání v kroku Zadání | 01, 03, 05, 14 |
| `ToolSelected` | uživatel | Ruční volba nástroje (karta, „Zadat ručně“): prázdný návrh v kroku Kontrola údajů | 01, 05, 07, 13 |
| `EditRequested` | uživatel | „Upravit údaje“: návrh se stejnými hodnotami jako potvrzená zakázka | 01, 07, 13 |
| `RoutingDecided`* | app (výsledek efektu) | `RoutingDecision`: schopnost a záměr | 01, 03, 05, 14 |
| `ProposalReceived` | app | Návrh změny od AI | 01, 02, 03 |
| `ClarificationReceived`* | app | Doplňující otázka místo návrhu | 03, 05 |
| `ProposalEdited`* | uživatel | Úprava buňky, řádku, parametru nebo cíle v návrhu | 01, 03, 08, 13 |
| `ProposalConfirmed` | uživatel | „Potvrdit a vypočítat“, nová revize | 01, 02, 03 |
| `ProposalRejected` | uživatel | „Zahodit změny“ | 03 |
| `SolveRequested` | app / uživatel | Spuštění výpočtu, „Přepočítat“ | 01, 03 |
| `SolveFinished` | app | Výsledek solveru | 01, 02, 03 |
| `SolveFailed`* | app | Neočekávaná chyba solveru | 01 |
| `OperationCancelled`* | uživatel | Zrušení běžícího AI volání, výpočtu nebo PDF | 01, R5 |
| `AiFailed` | app | Selhání AI s druhem chyby | 07 |
| `RetryRequested`* | uživatel | Opakování poslední neúspěšné operace | 07 |
| `CostInputsChanged`* | uživatel | Změna práce, nákladů, přirážky nebo DPH (přímo, R2) | 04 |
| `PdfRequested`* / `PdfRendered`* / `PdfFailed`* | uživatel / app | Export PDF | 04 |
| `ProjectImported` | uživatel / app | Načtení souboru nebo příkladu; obsah ověří jádro, neplatný soubor nastaví jen chybu načtení | 06, 10 |
| `ExampleOpened`* | uživatel | Výběr příkladu | 10 |
| `ExplanationReceived`* | app | Odpověď na dotaz k výsledku | 14 |
| `ProjectRenamed`* | uživatel | Přejmenování zakázky v Hlavičce (nemění vstupy plánu) | 06, 15 |
| `ProjectSaved` | uživatel | Soubor zakázky stažený v dané revizi; podklad pro „neuložené změny“ | 06, 15 |
| `NewProjectRequested` | uživatel | Nová zakázka, ukončení dema; na neuložené změny se UI ptá předem | 11, 15 |
| `RouterSwitched`* | uživatel | Přepnutí implementace routeru | 07, 12 |
| `StockChangeProposed`* / `StockChangeConfirmed`* / `StockChangeRejected`* | uživatel | Úprava skladu, odepsání po výrobě | 08, 16 |

| Efekt | Port / adaptér | Výsledná událost |
|---|---|---|
| `CallRouter` | Router (Jev / Layo / LLM) | `RoutingDecided`*, `AiFailed` |
| `CallExtractor` (nová zakázka / změna) | Generativní LLM (Groq) | `ProposalReceived`, `ClarificationReceived`*, `AiFailed` |
| `CallExplainer`* | Generativní LLM | `ExplanationReceived`*, `AiFailed` |
| `RunSolver` | Registr schopností (v `app/`, mimo reducer kvůli času) | `SolveFinished`, `SolveFailed`* |
| `RenderPdf` | PDF (WeasyPrint) | `PdfRendered`*, `PdfFailed`* |
| `LoadExample`* | Úložiště příkladů | `ProjectImported` |
| `WriteStock`* | Úložiště skladu (SQLite) | `StockChangeConfirmed`* / chyba |

Uložení zakázky do JSON je čtení stavu (endpoint vrací soubor), ne událost. Přepočet kalkulace po `CostInputsChanged`* je čistá funkce v reduceru, ne efekt.
