# Persony a jejich úkoly (jobs to be done)

**Stav:** schváleno  
**Vychází z:** specifikace v0.3, kap. 2 (cíloví uživatelé), kap. 9 (použitelnost), kap. 12 (obhajoba)

Persony jsou **archetypy**, ne konkrétní lidé. Primární persony určují, jak má vypadat hlavní tok. Vedlejší persony zdůvodňují podpůrné části aplikace: demo režim, příklady, první spuštění a vývojářský panel. Kde se zájmy střetnou, mají přednost primární persony.

| Kód | Persona | Typ | Hlavní schopnost |
|---|---|---|---|
| P1 | Zámečník v malé kovodílně | primární | Řezání tyčí (`cutting_1d`) |
| P2 | Truhlář nebo domácí dílna | primární, rozšíření | Řezání desek (`cutting_2d`) |
| P3 | Majitel malé dílny | primární | Kalkulace, sklad (rozšíření) |
| S1 | Hodnotitel u obhajoby | vedlejší | Demo, příklady |
| S2 | Vývojář a autor projektu | vedlejší | Vývojářský panel |
| S3 | Testovací uživatel | vedlejší | První spuštění bez nápovědy |

Jobs to be done jsou psané ve tvaru **„Když …, chci …, abych …“**. Kódy (J1.1 …) používají use cases a user flows.

---

## P1 — Zámečník v malé kovodílně

**Kontext.** Pracuje sám nebo s jedním pomocníkem. Dělá ploty, brány, zábradlí, rámy a regály z jeklů, L profilů a kulatiny. Materiál nakupuje v hutním skladu v tyčích 6 m, někdy 3 m nebo 12 m. Zakázky domlouvá po telefonu nebo na místě a míry si píše na papír. Aplikaci otevře v dílně na notebooku, obvykle večer před nákupem materiálu.

**Cíl.** Zjistit, kolik tyčí koupit a jak je nařezat, aby zbylo co nejméně odpadu a nic nechybělo.

**Co dnes dělá ručně.**
- Sečte délky na papíře nebo v kalkulačce a vydělí délkou tyče.
- Díly do tyčí rozkládá odhadem („dva po dvou metrech a jeden po metru a půl“).
- Na prořez pilou zapomíná nebo ho odhaduje.
- Seznam řezů si píše křídou nebo na papír k pile.

**Frustrace.**
- Na konci chybí kus a musí znovu do skladu, nebo naopak zbude zbytečná tyč.
- Při změně zakázky („přidejte ještě dvě příčky“) počítá všechno znovu.
- Tabulkové nástroje a specializované programy jsou na jednu zakázku příliš složité.
- Nevěří výsledku, který neumí ověřit. Chce vidět, co přesně se kde řeže.

**Technická zdatnost.** Nízká až střední. Ovládá telefon, e-mail a webový prohlížeč, tabulky jen základně. Nezná pojmy jako „router“, „model“ nebo „revize“. Píše hovorově, s jednotkami různě („2 m“, „200 cm“, „dva metry“).

**Jobs to be done.**
- **J1.1** Když mám od zákazníka seznam dílů, chci ho napsat vlastními slovy, abych ho nemusel přepisovat do formuláře.
- **J1.2** Když aplikace údaje přečte, chci je rychle zkontrolovat a opravit, abych měl jistotu, že počítá se správnými čísly.
- **J1.3** Když jedu nakupovat, chci vědět, kolik tyčí jaké délky koupit, abych nejel dvakrát.
- **J1.4** Když řežu, chci mít u pily přehledný plán řezů, abych nepočítal z hlavy.
- **J1.5** Když se zakázka změní, chci jen napsat, co je jinak, abych nemusel zadávat všechno znovu.

**Co z toho plyne pro design.**
- Textové pole je hlavní vstup. Ruční formulář je rovnocenná cesta, ne nouzovka.
- Kontrolní tabulka musí být rychle čitelná: díl, délka, počet, vždy s jednotkou.
- Plán musí být měřítkový a tisknutelný (PDF), s pořadím řezů na tyči.
- Žádné interní pojmy v hlavním UI.

---

## P2 — Truhlář nebo domácí dílna *(rozšíření UC-02)*

**Kontext.** Řemeslník na živnostenský list nebo zručný kutil. Vyrábí police, jednoduché skříně a pracovní stoly z lamina, překližky nebo MDF. Desky kupuje ve formátu (např. 2800 × 2070 mm) a často si je nechává nařezat v prodejně podle nářezového plánu.

**Cíl.** Rozmístit díly na co nejmenší počet desek a dostat plán, podle kterého lze řezat nebo ho předat prodejně.

**Co dnes dělá ručně.**
- Kreslí desky na čtverečkovaný papír a díly do nich zakresluje.
- Používá online nástroje prodejců, které jsou vázané na jejich sortiment.
- Kvůli směru dekoru (léta dřeva) musí hlídat, které díly se nesmí otočit.

**Frustrace.**
- Zakreslování trvá a snadno se splete o prořez.
- Rozmístění z jednoduchých nástrojů nejde nařezat na formátovací pile, protože řezy nejsou průběžné.
- Při změně rozměru jednoho dílu musí kreslit znovu.

**Technická zdatnost.** Střední. Zvyklý na online konfigurátory a e-shopy, občas pracuje v jednoduchém CAD nebo SketchUpu.

**Jobs to be done.**
- **J2.1** Když mám seznam dílů z výkresu, chci ho zadat najednou včetně omezení otáčení, abych nehlídal dekor ručně.
- **J2.2** Když dostanu rozmístění, chci vědět, že jde opravdu nařezat (gilotinové řezy), abych neplýtval deskou.
- **J2.3** Když nechávám řezat v prodejně, chci plán vytisknout s rozměry a pořadím řezů, aby mu prodejna rozuměla.

**Co z toho plyne pro design.**
- Kontrolní tabulka potřebuje u dílu přepínač „lze otočit“.
- Výsledek rozlišuje „nářezový plán“ (ověřený postup řezů) a „rozložení dílů“.
- Plán desky musí ukazovat i pořadí řezů a ořez okrajů.

---

## P3 — Majitel malé dílny

**Kontext.** Vede dílnu s několika lidmi, sám ale stále vyrábí. Kromě výroby dělá nabídky zákazníkům a hlídá náklady. V dílně má regál se zbytky z dřívějších zakázek, které by rád využil, ale nemá přehled, co tam leží.

**Cíl.** Rychle připravit orientační cenu zakázky pro zákazníka a přitom využít materiál, který už má.

**Co dnes dělá ručně.**
- Cenu počítá v tabulce: materiál, hodiny práce, přirážka, DPH.
- Ceny materiálu opisuje z ceníku dodavatele.
- Zbytky eviduje zpaměti nebo vůbec. Kontroluje je pohledem do regálu.

**Frustrace.**
- Nabídka je hotová pozdě, protože čeká na výpočet materiálu.
- Když zákazník změní rozsah, musí přepočítat materiál i cenu.
- Nakupuje materiál, který už má ve zbytcích.
- Nástroje typu ERP jsou pro jeho velikost drahé a složité.

**Technická zdatnost.** Střední. Pracuje s tabulkami, účetním programem a e-mailem. Chce mít čísla pod kontrolou a vidět, odkud se vzala.

**Jobs to be done.**
- **J3.1** Když zákazník chce cenu, chci z plánu rychle dostat rozpad nákladů, abych mohl poslat nabídku ještě dnes.
- **J3.2** Když zadávám ceny a sazby, chci, aby aplikace nic nedomýšlela, abych za cenou mohl stát.
- **J3.3** Když chybí cena některé položky, chci to jasně vidět, abych neposlal neúplnou nabídku.
- **J3.4** *(rozšíření UC-08)* Když mám na skladě zbytky, chci, aby je výpočet použil jako první, abych zbytečně nenakupoval.
- **J3.5** *(rozšíření UC-08)* Když je zakázka vyrobená, chci zapsat nové zbytky do skladu, abych o nich příště věděl.
- **J3.6** Když se k zakázce vrátím za týden, chci ji otevřít a pokračovat, abych nezačínal znovu.

**Co z toho plyne pro design.**
- Kalkulace ukazuje cenové předpoklady a chybějící položky („chybí cena“, nikdy 0 Kč).
- Každá částka je dohledatelná ze zobrazených vstupů.
- Uložení a načtení zakázky musí být snadno dostupné, ne schované v menu.
- Sklad se mění jen po výslovném potvrzení a změny jsou dohledatelné.

---

## S1 — Hodnotitel u obhajoby

**Kontext.** Vyučující předmětu GenAI. Aplikaci vidí poprvé při obhajobě nebo ji spouští sám podle README. Má na ni jen několik minut a hodnotí hlavně kvalitu a použitelnost UI (`docs/zadani.md`) a splnění AI kritérií.

**Cíl.** Rychle pochopit, co aplikace dělá, a vidět hlavní tok i práci AI bez nutnosti vymýšlet zadání.

**Co dnes dělá.** Prochází mnoho semestrálních prací, často nefunkčních bez klíčů nebo sítě.

**Frustrace.**
- Aplikace, která bez API klíče nebo sítě nic neukáže.
- Prázdná obrazovka bez náznaku, co napsat.
- Demo vydávané za živé volání modelu.

**Technická zdatnost.** Vysoká. Zná LLM, strukturovaný výstup a evaluace a chce vidět, jak jsou použité.

**Jobs to be done.**
- **JS1.1** Když aplikaci otevřu, chci jedním klikem spustit připravený příklad, abych hned viděl celý tok.
- **JS1.2** Když nemám klíče ani síť, chci demo, které je zřetelně označené, abych věděl, co je živé a co připravené.
- **JS1.3** Když mě zajímá AI část, chci se podívat „pod kapotu“ (router, prompt, trasování), aniž by to rušilo běžné UI.

**Co z toho plyne pro design.**
- Úvodní obrazovka nabízí příklady a demo na první pohled.
- Demo režim má trvalé a viditelné označení.
- Vývojářský panel je dostupný, ale v hlavním toku nepřekáží.

---

## S2 — Vývojář a autor projektu

**Kontext.** Student, který aplikaci staví. Ladí prompty v Langfuse, porovnává implementace routeru (Jev, LLM, ruční) a předvádí aplikaci u obhajoby.

**Cíl.** Vidět, proč aplikace rozhodla, jak rozhodla, a rychle přepnout implementaci routeru.

**Co dnes dělá.** Hledá v logu a v Langfuse, které volání patří ke kterému kroku.

**Frustrace.**
- Rozhodnutí routeru nebo validace nejsou z UI vidět.
- Přepnutí routeru vyžaduje restart nebo úpravu konfigurace.

**Technická zdatnost.** Vysoká.

**Jobs to be done.**
- **JS2.1** Když aplikace zvolí nástroj, chci vidět rozhodnutí routeru s pravděpodobnostmi, abych mohl ladit prahy.
- **JS2.2** Když chci porovnat routery, chci je přepnout za běhu, abych to ukázal i u obhajoby.
- **JS2.3** Když něco selže, chci vidět stav validace, verzi promptu a odkaz na trace, abych chybu našel.
- **JS2.4** Když řeším solver, chci vidět počet vzorů, dolní mez a stav CP-SAT.

**Co z toho plyne pro design.**
- Vývojářský panel je oddělený a obsahuje vše z kap. 8 specifikace (diagnostika bez tajných údajů).
- Přepínač routeru je ve vývojářském panelu (a v nastavení).

---

## S3 — Testovací uživatel

**Kontext.** Člověk mimo projekt, který podle kap. 9 specifikace zkouší vytvoření a změnu zakázky bez nápovědy. Může to být řemeslník (blízko P1 nebo P3) nebo spolužák. Aplikaci vidí poprvé.

**Cíl.** Splnit zadaný úkol („vytvořte plán pro plot a pak přidejte dvě příčky“) bez vysvětlování.

**Frustrace.**
- Neví, co má napsat a v jakém tvaru.
- Neví, ve kterém kroku je a co má udělat dál.
- Nerozumí, proč výsledek „zešedl“ (neaktuální) nebo proč nejde stáhnout PDF.

**Technická zdatnost.** Různá, typicky střední.

**Jobs to be done.**
- **JS3.1** Když aplikaci otevřu poprvé, chci hned vědět, co mám udělat, abych nepotřeboval návod.
- **JS3.2** Když se něco změní (výsledek je neaktuální, AI selže), chci vědět proč a co dál, abych se nezasekl.

**Co z toho plyne pro design.**
- Ukazatel kroků (Zadání → Kontrola údajů → Plán a cena) je vždy viditelný.
- Každý stav má jednu zřejmou další akci.
- Prázdné stavy obsahují příklad, ne jen prázdné místo.

---

## Souhrn: úkoly × části aplikace

| Část aplikace | P1 | P2 | P3 | S1 | S2 | S3 |
|---|---|---|---|---|---|---|
| Textové zadání | J1.1 | J2.1 | | JS1.1 | | JS3.1 |
| Ruční formulář | J1.2 | J2.1 | J3.2 | | | |
| Kontrola údajů | J1.2 | J2.1 | J3.2 | | | |
| Plán | J1.3, J1.4 | J2.2, J2.3 | | | JS2.4 | |
| Kalkulace | | | J3.1–J3.3 | | | |
| Dialog úprav | J1.5 | | | | | JS3.2 |
| Uložení a načtení | | | J3.6 | | | |
| PDF | J1.4 | J2.3 | J3.1 | | | |
| Sklad *(rozšíření)* | | | J3.4, J3.5 | | | |
| Příklady a demo | | | | JS1.1, JS1.2 | JS2.2 | JS3.1 |
| Vývojářský panel | | | | JS1.3 | JS2.1–JS2.4 | |
