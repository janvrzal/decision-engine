@AGENTS.md

## Specifika pro Claude Code

- Postupy jsou skilly v `.claude/skills/`; před odpovídající činností je načti:
  - `nova-schopnost` — přidání schopnosti do registru,
  - `overeni-solveru` — testování solverů,
  - `ai-evaluace` — práce s evaluačními sadami a reporty,
  - `zmena-specifikace` — úprava `docs/specifikace.md`,
  - `adr` — zápis architektonického rozhodnutí,
  - `priprava-pr` — kontrola před commitem a PR.
- U změn zasahujících více vrstev nebo měnících datové objekty nejdřív navrhni plán a nech ho schválit.
- Nejasnost ve specifikaci řeš otázkou uživateli, ne vlastním výkladem.
