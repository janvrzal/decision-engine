@AGENTS.md

## Specifika pro Claude Code

- Postupy jsou skilly v `.claude/skills/`; před odpovídající činností je načti:
  - `ui-frontend` — práce na frontendu, vzhledu a UX,
  - `nova-schopnost` — přidání schopnosti do registru,
  - `overeni-solveru` — testování solverů,
  - `ai-evaluace` — prompty, evaluační sady a reporty,
  - `zmena-specifikace` — úprava `docs/specifikace.md`,
  - `adr` — zápis architektonického rozhodnutí,
  - `priprava-pr` — kontrola před commitem a PR.
- Každý svislý řez začíná plánem, který schválí uživatel (plan mode).
- Nejasnost ve specifikaci řeš otázkou uživateli, ne vlastním výkladem.
