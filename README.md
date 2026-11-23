# DecisionEngine

Webová aplikace pro malé dílny: ze zadání v češtině k nářezovému plánu a orientační ceně zakázky.

Semestrální práce. Stav: příprava repozitáře, implementace zatím nezačala.

- Specifikace: [docs/specifikace.md](docs/specifikace.md)
- Rozhodnutí: [docs/adr/](docs/adr/)
- Pravidla pro vývoj a AI agenty: [AGENTS.md](AGENTS.md)

## Spuštění vývojového prostředí

```bash
brew install uv
uv sync
uv run pre-commit install
uv run pytest
```
