# ADR-0007: Webové UI ve SvelteKitu nad FastAPI

**Stav:** přijato  
**Datum:** 2026-11-23  
**Souvisí se:** ADR-0006, specifikace kap. 4, 9, 10; `docs/zadani.md`

## Kontext

Kvalita a použitelnost UI je jediný povinný a výslovně hodnocený požadavek zadání. Aplikace potřebuje dialog vedle pracovní plochy, editovatelné tabulky, měřítkový plán v SVG a jasné stavy. Streamlit (původní volba) nabízí omezenou kontrolu nad vzhledem a interakcí a jeho model překreslování celé stránky komplikuje správu stavu.

## Rozhodnutí

- **Backend:** FastAPI (Python), viz ADR-0006. Typy API popisuje OpenAPI generované z Pydantic modelů.
- **Frontend:** SvelteKit se Svelte 5 a TypeScriptem ve strict režimu, v režimu SPA (`adapter-static`, bez SSR). Sestavený frontend servíruje FastAPI, takže aplikace se spouští jedním příkazem.
- **Vzhled:** Tailwind CSS s design tokeny (barvy, typografie, rozestupy) a komponenty shadcn-svelte (Bits UI), které jsou přístupné a upravitelné.
- **Klient API:** typy generované z OpenAPI (`openapi-typescript`) a typovaný `openapi-fetch`; ruční psaní typů API je zakázané.
- **Nástroje frontendu:** pnpm, ESLint, Prettier, `svelte-check`, Vitest pro logiku komponent, Playwright pro end-to-end testy hlavního toku.
- **Plán:** SVG generuje backend čistou funkcí (`render_svg`), stejné SVG použije PDF. Frontend ho jen zobrazí a doplní interakci (zvýraznění dílu, popisky).
- **Struktura:** monorepo, Python v `src/`, frontend v `frontend/`.
- **Nasazení:** jen lokálně.

## Zvažované varianty

- **Streamlit** — nejrychlejší, ale nejméně kontroly nad vzhledem a stavem.
- **NiceGUI** — Python a slušné komponenty, ale vzhled omezený Quasarem a menší ekosystém.
- **FastAPI + HTMX** — jeden jazyk, ale editovatelné tabulky a dialog jsou pracné.
- **React** — srovnatelné se SvelteKitem; Svelte má méně boilerplate a jednodušší reaktivitu.

## Důsledky

- Dva jazyky a dvojí tooling; CI kontroluje Python i frontend.
- Frontend je tenký: zobrazuje stav a posílá události. Formátování čísel a jednotek (`Intl`, `cs-CZ`) je jediná „logika“ ve frontendu.
- Odhadem o třetinu víc práce na UI než se Streamlitem, výměnou za plnou kontrolu nad vzhledem.
