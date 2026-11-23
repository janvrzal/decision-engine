---
name: adr
description: Zápis architektonického rozhodnutí (ADR) v DecisionEngine do docs/adr/. Použij při volbě technologie, knihovny, algoritmu, formátu dat, hranice vrstev nebo když se mění dříve přijaté rozhodnutí.
---

# Zápis ADR

## Kdy psát ADR

- Nová závislost (knihovna, poskytovatel AI, služba).
- Volba algoritmu nebo modelu úlohy (solver, cíl optimalizace).
- Změna datového formátu, hranic vrstev nebo pravidel z `AGENTS.md`.
- Rozhodnutí, u kterého by se za měsíc někdo zeptal „proč to je takhle?“.

Drobné implementační volby uvnitř jednoho modulu ADR nepotřebují; stačí komentář v kódu.

## Postup

1. Další volné číslo zjistíš z `ls docs/adr/`. Soubor `NNNN-kratky-nazev.md` (bez diakritiky v názvu souboru).
2. Zkopíruj `docs/adr/0000-sablona.md` a vyplň: kontext, rozhodnutí, zvažované varianty (alespoň dvě, včetně té zamítnuté), důsledky.
3. Stav: `navrženo`, dokud ho uživatel neschválí; pak `přijato`.
4. Rozhodnutí formuluj ověřitelně. U každého pravidla uveď, co ho hlídá mechanicky (lint, test, CI), a co zůstává na disciplíně.
5. Nahrazuje-li dřívější ADR: starý **nepřepisuj**, jen mu změň stav na `nahrazeno ADR-NNNN`.
6. Pokud ADR mění pravidla v `AGENTS.md` nebo chování ve specifikaci, uprav je ve stejném PR.

Commit: `docs(adr): přidat ADR-NNNN …`.
