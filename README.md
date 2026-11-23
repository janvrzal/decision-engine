# DecisionEngine

Webová aplikace pro malé dílny: ze zadání v češtině k nářezovému plánu a orientační ceně zakázky.

Semestrální práce. Stav: kostra aplikace (milník M0).

Backend: Python 3.12 + FastAPI. Frontend: SvelteKit (Svelte 5, TypeScript). Lokální běh.

- Specifikace: [docs/specifikace.md](docs/specifikace.md)
- Rozhodnutí: [docs/adr/](docs/adr/)
- Pravidla pro vývoj a AI agenty: [AGENTS.md](AGENTS.md)

## Spuštění

Potřebujete `uv`, `pnpm` a Node.js 22+ (`brew install uv pnpm node`).

```bash
uv sync
pnpm -C frontend install
pnpm -C frontend build
uv run decision-engine
```

Aplikace běží na <http://127.0.0.1:8000>.

## Vývoj

```bash
uv run pre-commit install
uv run decision-engine          # backend na :8000
pnpm -C frontend dev            # frontend s hot reloadem, /api přes proxy na :8000
```

Kontroly backendu a frontendu jsou v [AGENTS.md](AGENTS.md#příkazy).
