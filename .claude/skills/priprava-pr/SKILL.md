---
name: priprava-pr
description: Kontrola před commitem a otevřením pull requestu v DecisionEngine — spuštění všech kontrol, revize diffu, Conventional Commits a popis PR. Použij, když je změna hotová a má se commitovat nebo z ní má vzniknout PR.
---

# Příprava commitu a PR

Commit a push děláš jen na pokyn uživatele.

## 1. Větev

- Nejsi na `main`. Pokud ano, založ větev podle `AGENTS.md` (`feat/…`, `fix/…` …).
- Jedna větev = jedna logická změna. Nesouvisející úpravy patří jinam.

## 2. Kontroly (všechny musí projít)

Backend:

```bash
uv run ruff check
uv run ruff format --check
uv run pyright
uv run lint-imports
uv run pytest
```

Frontend (ve `frontend/`, pokud se změna týká frontendu nebo API):

```bash
pnpm generate:api   # po změně API; vygenerované typy patří do PR
pnpm check
pnpm lint
pnpm test
pnpm test:e2e       # při změně hlavního toku
```

Nevynechávej selhávající test ani ho neoznačuj `skip`/`xfail` bez souhlasu uživatele. Neobcházej pre-commit (`--no-verify`).

## 3. Revize vlastního diffu

Projdi `git diff main...HEAD` a ověř:

- [ ] žádné tajné údaje, `.env`, výpisy s klíči, osobní data,
- [ ] žádný ladicí kód (`print`, zakomentované bloky, `breakpoint()`),
- [ ] jádro neporušuje pravidla z `AGENTS.md` (I/O, čas, náhoda, mutovatelná data, výjimky ven, `float` pro délky/peníze),
- [ ] uživatelské texty česky a srozumitelně,
- [ ] změna UI ověřená v běžící aplikaci podle checklistu ve skillu `ui-frontend` (do PR stačí popis, screenshoty se nepřikládají),
- [ ] frontend nic nepočítá a typy API jsou vygenerované, ne psané ručně,
- [ ] specifikace a ADR odpovídají (skilly `zmena-specifikace`, `adr`),
- [ ] testovací AI sady nebyly použity k ladění (skill `ai-evaluace`).

## 4. Commit

Conventional Commits, typ a scope anglicky, popis česky v rozkazovacím způsobu, max. ~72 znaků:

```
feat(cutting_1d): přidat FFD pro více skladových délek

Proč je změna potřeba a co neřeší (volitelně).
```

Typy: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `eval`. Scope: schopnost nebo vrstva (`cutting_1d`, `costing`, `router`, `app`, `api`, `frontend`, `prompts`, `spec`, `adr` …).

## 5. Pull request

Šablona je v `.github/pull_request_template.md`. Popis obsahuje:

- **Co a proč** — 2–4 věty, odkaz na kapitolu/UC specifikace,
- **Jak ověřeno** — jaké testy přibyly, ruční ověření v UI (na jakých šířkách a co se prošlo), evaluace (s odkazem na report),
- **Dopady** — změny formátu zakázky, specifikace, ADR, známá omezení.

Po otevření PR počkej na CI; neslučuj s červeným CI.
