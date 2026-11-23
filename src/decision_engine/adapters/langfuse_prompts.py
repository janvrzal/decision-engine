"""Prompty z Langfuse prompt managementu se záložní kopií z `prompts/` (ADR-0009)."""

from collections.abc import Mapping
from typing import Any, cast

from langfuse import Langfuse

from decision_engine.adapters.file_prompts import FilePromptStore
from decision_engine.app.ports import ChatMessage, Prompt

PRODUCTION_LABEL = "production"
CACHE_TTL_SECONDS = 300


class LangfusePromptStore:
    """Načte prompt se štítkem `production`; když Langfuse nedostupný, použije zálohu."""

    def __init__(self, client: Langfuse, fallback: FilePromptStore) -> None:
        self._client = client
        self._fallback = fallback

    def get(self, name: str, variables: Mapping[str, str]) -> Prompt:
        prompt_file = self._fallback.file(name)
        try:
            client_prompt = self._client.get_prompt(
                name,
                label=PRODUCTION_LABEL,
                type=prompt_file.type,
                fallback=cast(Any, prompt_file.prompt),
                cache_ttl_seconds=CACHE_TTL_SECONDS,
            )
        except Exception:  # SDK hlásí výpadek různými výjimkami; záloha musí fungovat vždy.
            return self._fallback.get(name, variables)

        compiled = cast(Any, client_prompt.compile(**variables))
        messages = (
            (ChatMessage(role="user", content=compiled),)
            if isinstance(compiled, str)
            else tuple(ChatMessage.model_validate(message) for message in compiled)
        )
        if client_prompt.is_fallback:
            return Prompt(
                name=name, version=prompt_file.version, source="fallback", messages=messages
            )
        return Prompt(
            name=name,
            version=client_prompt.version,
            source="langfuse",
            messages=messages,
            handle=client_prompt,
        )
