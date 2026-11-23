# Service design DecisionEngine

Podklady pro návrh a implementaci UI. Vycházejí ze specifikace v0.3 (`docs/specifikace.md`) a ADR-0006/0007. Při rozporu platí specifikace. Úpravy specifikace, které ze service designu vyplynuly, jsou na konci tohoto souboru.

| Dokument | Obsah | Stav |
|---|---|---|
| [01-persony.md](01-persony.md) | Persony (archetypy) a jejich jobs to be done | schváleno |
| [02-use-cases.md](02-use-cases.md) | UC-01 až UC-16, společná pravidla R1–R6, katalog událostí | schváleno |
| [03-user-flows.md](03-user-flows.md) | F0–F10: stavy zakázky, hlavní a další toky | schváleno |
| [04-mapa-obrazovek.md](04-mapa-obrazovek.md) | Obrazovky, panely, dialogy, stavy, navigace, kostra view modelu | schváleno |

**Wireframy a diagramy:** [FigJam board „DecisionEngine – service design a wireframy“](https://www.figma.com/board/8KDBbDBBHIaWt0VXLR50Kq). Obsahuje 41 low-fi rámců v sekcích A–G (úvod, zadání a Dialog, Kontrola údajů, Plán a cena, dialogy, sklad, vývojářský panel), každý s poznámkou s odkazem na UC, a diagramy F0–F2. Wireframy ukazují rozložení a stavy, ne vizuální styl. Ten určuje design systém.

## Slovník obrazovek a panelů

Tyto názvy používají všechny dokumenty, design systém i kód (identifikátory komponent v závorce). Názvy v UI se mohou zkrátit, v dokumentaci se nemění.

| Název | Typ | Identifikátor | Kde |
|---|---|---|---|
| Úvodní obrazovka | obrazovka | `HomeScreen` | `/` |
| Pracovní obrazovka zakázky | obrazovka | `ProjectScreen` | `/project` |
| Sklad *(rozšíření)* | obrazovka | `StockScreen` | `/stock` |
| Horní lišta | část obrazovky | `AppBar` | všude kromě celostránkových chyb |
| Hlavička zakázky | část obrazovky | `ProjectHeader` | Pracovní obrazovka |
| Ukazatel kroků | část obrazovky | `StepIndicator` | Pracovní obrazovka |
| Panel Dialog | panel | `ChatPanel` | Pracovní obrazovka vlevo |
| Pracovní plocha | oblast | `Workspace` | Pracovní obrazovka vpravo |
| Krok Zadání | stav pracovní plochy | `InputStep` | Pracovní plocha |
| Krok Kontrola údajů | stav pracovní plochy | `ReviewStep` | Pracovní plocha |
| Krok Plán a cena | stav pracovní plochy | `ResultStep` | Pracovní plocha |
| Panel Plán | panel | `PlanPanel` | Krok Plán a cena |
| Panel Kalkulace | panel | `CostPanel` | Krok Plán a cena |
| Souhrnná lišta | připnutá lišta | `ResultSummaryBar` | Krok Plán a cena, dole |
| Vývojářský panel | vysouvací panel | `DevPanel` | nad Pracovní obrazovkou |
| Pruh demo režimu | pruh | `DemoBanner` | všude v demu |
| Dialog Příklady | modální dialog | `ExamplesDialog` | z Úvodní obrazovky |
| Dialog Načíst zakázku | modální dialog | `ImportDialog` | Úvodní obrazovka, Hlavička |
| Dialog Zahodit rozpracovanou zakázku | modální dialog | `DiscardProjectDialog` | před novou / načtenou zakázkou |
| Dialog Zápis do skladu *(rozšíření)* | modální dialog | `StockWriteDialog` | Krok Plán a cena |
| Dialog Zahodit změny skladu *(rozšíření)* | modální dialog | `DiscardStockDialog` | Sklad |

Pojmy v UI: **zakázka** (ne projekt), **díl**, **tyč / skladová délka**, **prořez**, **zbytek** (využitelný) vs. **odpad**, **plán**, **kalkulace** (orientační), **verze** (v UI místo „revize“), **nástroj** (místo „schopnost“).

## Úpravy specifikace

Zjištění ze service designu, která mění chování. Byla schválena a promítnuta do specifikace v0.4.

1. **Vstupy plánu vs. vstupy kalkulace (R2).** Vstupy kalkulace (práce, další náklady, přirážka, DPH) se upravují přímo. Úprava vytvoří revizi a plán nezneplatní. Ceny skladových délek patří ke vstupům plánu. Týká se kap. 4 (Výsledek), 7 (Stav zakázky, aplikační vrstva) a UC-04.
2. **Neaktuální plán (R3).** Odvozená vlastnost se rozšiřuje: plán je neaktuální, pokud se změnily *vstupy plánu*, čeká nepotvrzený návrh, nebo se změnila revize skladu. Ceny skladových délek zneaktuální plán jen při cíli „nejnižší cena“; jinak jejich změna (potvrzená přímo v Panelu Kalkulace) přepočítá jen kalkulaci. Dnešní definice `result.revision != project.revision` by po R2 nestačila. Týká se kap. 7.
3. **Ruční úpravy jsou také návrh (R1).** Upřesnit v kap. 7 (Stav zakázky), že formulář i úprava buňky mění `ChangeProposal`, ne zakázku.
4. **Pořadí dílů na tyči v 1D plánu a PDF** (z persony P1). Doplnit do kap. 4 (Výsledek).
5. **Nové use cases UC-09 až UC-16** do kap. 5 v krátké podobě s odkazem sem.
