"""Prompty ze záložních kopií v `prompts/` (ADR-0009): aplikace běží i bez Langfuse."""

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, cast

from decision_engine.app.ports import ChatMessage, Prompt

_VARIABLE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class PromptFile:
    """Záložní kopie jednoho promptu ve formátu exportu z Langfuse."""

    def __init__(self, path: Path) -> None:
        data = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        self.name: str = data["name"]
        self.type: Literal["chat", "text"] = data["type"]
        self.version: int | None = data.get("version")
        self.prompt: str | list[dict[str, str]] = data["prompt"]

    def messages(self, variables: Mapping[str, str]) -> tuple[ChatMessage, ...]:
        """Zprávy s dosazenými proměnnými `{{nazev}}` (stejná syntaxe jako Langfuse)."""
        if isinstance(self.prompt, str):
            return (ChatMessage(role="user", content=compile_template(self.prompt, variables)),)
        return tuple(
            ChatMessage.model_validate(
                {**message, "content": compile_template(message["content"], variables)}
            )
            for message in self.prompt
        )


def compile_template(template: str, variables: Mapping[str, str]) -> str:
    """Dosadí proměnné; neznámé ponechá beze změny, aby chyba byla v trace vidět."""
    return _VARIABLE.sub(lambda match: variables.get(match.group(1), match.group(0)), template)


class FilePromptStore:
    """`PromptStore` nad složkou `prompts/`."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def file(self, name: str) -> PromptFile:
        return PromptFile(self._directory / f"{name}.json")

    def get(self, name: str, variables: Mapping[str, str]) -> Prompt:
        prompt_file = self.file(name)
        return Prompt(
            name=name,
            version=prompt_file.version,
            source="fallback",
            messages=prompt_file.messages(variables),
        )
