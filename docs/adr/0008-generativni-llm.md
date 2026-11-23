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
- Výchozí poskytovatel Groq, **výchozí model `qwen/qwen3.8-27b`**, záložní `openai/gpt-oss-120b` (spike #6, report [`evals/reports/2026-11-23-extraction-dev-modely.md`](../../evals/reports/2026-11-23-extraction-dev-modely.md)). Na dev sadě 18 českých zadání měl qwen nejvyšší úplnou shodu kritických polí (17/18 proti 15/18 a 14/18 u gpt-oss-120b a gpt-oss-20b), žádný vymyšlený údaj a nejkratší výstup; cena ~0,002 USD za extrakci je pro aplikaci zanedbatelná. Volba se potvrdí na testovací sadě v M8; změna modelu je jen hodnota `LLM_MODEL`.
- Strukturovaný výstup přes `response_format: json_object` a validaci Pydanticem: všechny tři modely daly 18/18 platných odpovědí bez opravy. `json_schema` výsledky nezlepšil a u qwen výstup rozbil, tool calling proto adaptér nepotřebuje.
- Výstup modelu se vždy validuje Pydanticem; při neplatném výstupu proběhne nejvýše jeden opravný pokus s chybami validace, pak `Err`.

## Zvažované varianty

- **LangChain / LiteLLM** — hotové přepínání poskytovatelů, ale další vrstva abstrakce a závislostí; potřebujeme jediné volání se schématem.
- **Groq SDK** — funguje jen pro Groq; OpenAI-kompatibilní klient pokryje víc poskytovatelů jedním kódem.

## Důsledky

- Výměna poskytovatele = změna konfigurace, případně nový adaptér; zbytek aplikace se nemění.
- Adaptér používá `json_object`; přechod na `json_schema` nebo tool calling by vyžadoval nové ověření, u `qwen/qwen3.8-27b` `json_schema` nefunguje spolehlivě.
- Free tier Groq má limity tokenů za minutu (8 000 TPM u gpt-oss, 1 000 výstupních TPM u qwen); pro jednoho uživatele stačí, evaluace musí volání rozkládat v čase.
