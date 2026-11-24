# Obsah a formáty

Texty v UI jsou součást designu. Píšou se z pohledu uživatele v dílně, ne z pohledu systému: člověk řeší *díly a tyče*, ne *schopnosti a revize*.

## Tón

- **Vykání**, věcně a krátce, jako zkušený kolega u ponku. Bez omluv, citoslovcí a nadšení („Skvělé!“).
- **Tlačítka a odkazy** jsou slovesa v rozkazovacím způsobu a říkají, co se stane: „Potvrdit a vypočítat“, „Stáhnout PDF“, „Zahodit změny“. Ne „OK“, „Ano“, „Odeslat formulář“.
- **Nadpisy** jsou podstatná jména nebo otázka v potvrzovacím okně: „Kontrola údajů“, „Zahodit rozpracovanou zakázku?“.
- **Asistent v dialogu** mluví v první osobě („Připravil jsem 2 díly…“) a vždy řekne, co odhadl a kde to uživatel ověří. Nikdy netvrdí víc, než ukazují data (AGENTS.md pravidlo 8).
- **Velká písmena** jen na začátku věty a u vlastních jmen; styl `label` převádí na velká písmena CSS, ne text.
- **Emoji** se nepoužívají; ikony jsou z Lucide a vždy doprovázejí slovo.

## Vzory textů

| Situace | Vzor | Příklad |
|---|---|---|
| Chyba | co se stalo + co udělat | „AI teď neodpovídá. Zkuste to za chvíli znovu, nebo vyplňte údaje ručně.“ „Ze zadání jsem nevyčetl díly k řezání. Uveďte díly s délkou a počtem a délku tyčí, nebo údaje vyplňte ručně.“ |
| Chyba pole | co doplnit nebo opravit, rozkazovacím způsobem | „Doplňte název dílu.“ „Délka musí být kladná.“ |
| Prázdný stav | co tu bude + jak to získat, jedna akce | „Plán zatím není spočítaný. Zkontrolujte díly a skladové délky.“ + „Vypočítat“ |
| Průběh | co se právě děje, nedokonavým slovesem s třemi tečkami | „Připravuji údaje ze zadání…“ „Hledám lepší plán…“ |
| Neaktivní akce | proč a co ji zpřístupní | „Výsledek je neaktuální, nejdřív přepočítejte.“ „Uložit půjde až potvrzenou zakázku. Nejdřív potvrďte údaje.“ |
| Názvy akcí | sloveso + předmět, stejná akce má všude stejný název | „Uložit zakázku“, „Načíst zakázku“, „Zpracovat zadání“, „Vytisknout plán“; panel s AI je „Asistent“ |
| Nápověda k pojmu | jedna věta pod popiskem pole, slovy dílny | „Kolik se uřízne z čela tyče, než začne první díl.“ |
| Potvrzení nevratné akce | otázka v nadpisu, následek v těle, akce pojmenovaná slovesem | „Zahodit rozpracovanou zakázku?“ … „Zahodit zakázku“ |
| Nepotvrzená hodnota | původ hodnoty konkrétně | „Výchozí hodnota, ověřte.“ „Odhad AI, ověřte.“ „Hodnota v souboru byla neplatná, ověřte.“ |
| Chybějící údaj | slovy, nikdy nula | „chybí cena“, „—“ s vysvětlením |

## Čísla a jednotky

Formátuje jen frontend přes `Intl.NumberFormat('cs-CZ')`; hodnoty počítá backend. Mezi číslem a jednotkou je nezlomitelná mezera, oddělovač tisíců je nezlomitelná mezera.

| Veličina | Formát | Příklad | Pravidla |
|---|---|---|---|
| Délka | celé mm | `1 250 mm` | Vždy mm. U délek od 10 m volitelně metry v podtextu: `12 500 mm` / `12,5 m`. V plánu bez jednotky u každého čísla, jednotka je v souhrnu a legendě. |
| Počet kusů | celé číslo + `ks` | `10 ks` | V textu „10× sloupek“, v tabulce sloupec Počet s `ks`. |
| Peníze | dvě desetinná místa + `Kč` | `1 234,50 Kč` | Chybějící cena je „chybí cena“, nikdy `0 Kč`. Sazba: `450 Kč/h`. |
| Procenta | jedno desetinné místo + ` %` | `91,7 %` | Mezera před `%`. Přirážka a DPH jako celé číslo, pokud je celé: `21 %`. |
| Čas výpočtu | sekundy, jedno desetinné místo | `3,5 s z 10 s` | |
| Datum a čas | `23. 11. 2026, 14:05` | | Mezery po tečkách, 24hodinový čas. |
| Rozměr profilu | `×` bez mezer | `40×40×2` | |
| Rozsah | spojovník bez mezer | `Tyč 1–4` | Pomlčka (–), ne minus. |

Uvozovky jsou české („…“, uvnitř ‚…‘), tři tečky jako jeden znak (…).

## Glosář

Pojem v UI je to, co uživatel vidí. Interní pojmy patří jen do kódu, specifikace a vývojářského panelu.

| Pojem v UI | Význam | Interní pojem / identifikátor | Nepoužívat v UI |
|---|---|---|---|
| zakázka | jedna úloha uživatele se všemi vstupy a výsledky | `Project` | projekt, úloha |
| zadání | text, kterým uživatel zakázku popíše | vstup routeru a extrakce | prompt, dotaz |
| nástroj | typ výpočtu, např. „Řezání tyčí“, „Kalkulace“ | schopnost, `cutting_1d` | schopnost, modul, capability |
| díl | kus, který se má vyrobit (název, délka, počet) | `Problem` (požadované díly) | položka, request |
| tyč, skladová délka | vstupní materiál dané délky | `Problem` (vstupní formáty) | stock, polotovar |
| prořez | šířka materiálu, kterou odebere řez | `Parameters` (prořez) | kerf |
| řez | místo, kde se tyč dělí; v plánu s polohou od začátku tyče | — | |
| využitelný zbytek, zbytek | zbytek tyče od minimální délky (výchozí 300 mm) | `Parameters` (minimální délka využitelného zbytku) | remnant |
| odpad | zbytek kratší než minimální délka a prořezy | — | ztráta, waste |
| výtěžnost | podíl délky dílů na spotřebované délce tyčí | metrika výsledku | yield, využití |
| cíl optimalizace | co plán minimalizuje: „Nejnižší cena“, „Nejméně tyčí“, „Nejméně materiálu“ | `Parameters` (cíl optimalizace: `cheapest`, `fewest_bars`, `least_material`) | objective |
| plán | nářezový plán tyčí | `CalculationResult` | výsledek solveru, řešení |
| Optimální | štítek plánu s prokázaným optimem | stav řešení v `CalculationResult` | |
| Nejlepší nalezený | štítek plánu bez prokázaného optima, s rozdílem od dolní meze | stav řešení v `CalculationResult` | heuristický, suboptimální |
| Částečný | štítek plánu, ve kterém se některé kusy nevešly | stav řešení, neumístěné kusy | |
| Bez řešení | štítek, když žádný proveditelný plán neexistuje | stav řešení | infeasible |
| neaktuální | plán neodpovídá potvrzeným vstupům | odvozená vlastnost (kap. 7) | stale, zastaralý |
| návrh změny | změna od AI nebo z ruční úpravy, která čeká na potvrzení | `ChangeProposal` | proposal |
| nepotvrzená hodnota | výchozí hodnota nebo odhad AI, který uživatel ještě neověřil | — | default, inferred |
| verze | stav potvrzených vstupů zakázky („Změny oproti verzi 2“) | revize | revize |
| kalkulace | orientační cena materiálu, práce a dalších nákladů | `CostEstimate` | rozpočet, nabídka |
| předpoklady | podmínky, za kterých kalkulace platí | cenové předpoklady | |
| sklad *(rozšíření)* | evidence tyčí a zbytků k dispozici | `StockItem` | inventory |
| demo | režim s připravenými daty bez volání AI | — | mock, fake |

Pojmy router, model, prompt, tokeny, trace, revize a názvy schopností se zobrazují jen ve vývojářském panelu. Identifikátory stavů řešení zatím specifikace neurčuje; komponenta `SolutionStatusBadge` je převezme z view modelu.
