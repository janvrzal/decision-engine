# ADR-0005: Nástroje a pracovní postup

**Stav:** přijato  
**Datum:** 2026-11-23

## Kontext

Projekt vyvíjí jeden autor s pomocí AI agentů. Chceme, aby kvalitu hlídaly nástroje, ne jen disciplína.

## Rozhodnutí

- Python 3.12, správa prostředí `uv`, závislosti v `pyproject.toml` a `uv.lock`.
- `ruff` (lint + formát), `pyright` ve strict režimu, `import-linter` pro hranice vrstev.
- `pytest` + `hypothesis` + `pytest-cov`; marker `ai` pro placená API, ve výchozím běhu vypnutý.
- `pre-commit` spouští ruff, pyright, lint-imports a kontrolu tajných údajů.
- GitHub: větev na každou změnu, PR s CI, Conventional Commits (popis česky).
- Jazyk: identifikátory anglicky, vše ostatní česky.
- Agent: Claude Code; pravidla v `AGENTS.md` (načítané z `CLAUDE.md`), postupy ve skillech `.claude/skills/`.

## Důsledky

- CI je stejné jako lokální kontroly; co projde lokálně, projde v CI.
- Strict pyright vyžaduje typové anotace i v testech; pro knihovny bez typů (OR-Tools) se použijí lokální stuby nebo cílené `# pyright: ignore[...]` s komentářem.
