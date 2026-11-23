# Frontend

SvelteKit (Svelte 5, TypeScript strict) jako SPA (`adapter-static`, bez SSR). Sestavený frontend servíruje backend příkazem `uv run decision-engine`. Konvence jsou ve skillu `.claude/skills/ui-frontend/`, rozhodnutí v ADR-0007 a ADR-0010, vzhled v `docs/design-system/`.

| Příkaz                      | Co dělá                                                                        |
| --------------------------- | ------------------------------------------------------------------------------ |
| `pnpm dev`                  | vývojový server; `/api` jde přes proxy na `http://127.0.0.1:8000`              |
| `pnpm build`                | sestaví SPA do `build/`                                                        |
| `pnpm generate:api`         | vygeneruje `src/lib/api/schema.d.ts` z OpenAPI backendu (commituje se)         |
| `pnpm check`                | svelte-check a TypeScript                                                      |
| `pnpm lint` / `pnpm format` | Prettier a ESLint                                                              |
| `pnpm test`                 | Vitest (unit v Node, komponenty `*.svelte.spec.ts` v prohlížeči)               |
| `pnpm test:e2e`             | Playwright proti `uv run decision-engine` se sestaveným frontendem, včetně axe |

Struktura: `src/lib/api/` klient API (generovaný), `src/lib/format.ts` formátování `cs-CZ`, `src/lib/components/` komponenty, `src/routes/` stránky, `e2e/` end-to-end testy.
