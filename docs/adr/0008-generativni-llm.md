# ADR-0008: Generativní LLM přes Groq za vyměnitelným adaptérem

**Stav:** přijato  
**Datum:** 2026-11-23  
**Souvisí se:** ADR-0004, ADR-0006, specifikace kap. 6

## Kontext

Extrakce, návrhy změn a doptávání potřebují generativní model se strukturovaným výstupem. Autor používá Groq, ale poskytovatele chce mít možnost kdykoli přepnout.

## Rozhodnutí

- Port `LlmClient` v `app/` s metodou pro strukturovaný výstup: vstupem jsou zprávy a Pydantic schéma, výstupem `Result[Model, LlmError]`.
- Výchozí implementace `OpenAICompatibleLlm` (oficiální SDK `openai`, konfigurovatelné `base_url`, model a klíč). Pokrývá Groq a také OpenAI a lokální servery (Ollama, LM Studio).
- Poskytovatele s vlastním API (např. Anthropic, Gemini) lze přidat jako další adaptér za stejný port.
- Výchozí poskytovatel Groq; konkrétní model se zvolí podle evaluace extrakce na dev sadě (spolehlivost JSON schématu, čeština) a zapíše se do reportu.
- Výstup modelu se vždy validuje Pydanticem; při neplatném výstupu proběhne nejvýše jeden opravný pokus s chybami validace, pak `Err`.

## Zvažované varianty

- **LangChain / LiteLLM** — hotové přepínání poskytovatelů, ale další vrstva abstrakce a závislostí; potřebujeme jediné volání se schématem.
- **Groq SDK** — funguje jen pro Groq; OpenAI-kompatibilní klient pokryje víc poskytovatelů jedním kódem.

## Důsledky

- Výměna poskytovatele = změna konfigurace, případně nový adaptér; zbytek aplikace se nemění.
- Podporu strukturovaného výstupu (JSON schema / tool calling) je nutné ověřit pro zvolený model; adaptér musí umět obojí.
