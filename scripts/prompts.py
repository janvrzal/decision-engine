"""Správa promptů v Langfuse (ADR-0009, skill `ai-evaluace`).

    uv run --env-file .env python scripts/prompts.py push <nazev> [--label staging]
    uv run --env-file .env python scripts/prompts.py promote <nazev> <verze>
    uv run --env-file .env python scripts/prompts.py export

`push` nahraje prompt z `prompts/<nazev>.json` jako novou verzi s daným štítkem.
`promote` přidá ověřené verzi štítek `production` (aplikace pak používá ji).
`export` stáhne všechny prompty se štítkem `production` zpět do `prompts/` (záložní kopie,
commituje se, aby změna promptu byla vidět v PR).
"""

import argparse
import json
from pathlib import Path
from typing import Any, cast

from langfuse import Langfuse

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def push(client: Langfuse, name: str, label: str, message: str | None) -> None:
    data = cast(dict[str, Any], json.loads((PROMPTS_DIR / f"{name}.json").read_text("utf-8")))
    created = cast(
        Any,
        client.create_prompt(
            name=name,
            prompt=data["prompt"],
            type=data["type"],
            labels=[label],
            config=data.get("config") or {},
            commit_message=message,
        ),
    )
    print(f"{name}: nahrána verze {created.version} se štítkem {label}")


def promote(client: Langfuse, name: str, version: int) -> None:
    client.update_prompt(name=name, version=version, new_labels=["production"])
    print(f"{name}: verze {version} má štítek production; spusťte export")


def export(client: Langfuse) -> None:
    for path in sorted(PROMPTS_DIR.glob("*.json")):
        data = cast(dict[str, Any], json.loads(path.read_text("utf-8")))
        prompt = cast(Any, client.get_prompt(data["name"], label="production", type=data["type"]))
        exported: dict[str, Any] = {
            "name": prompt.name,
            "type": data["type"],
            "version": prompt.version,
            "labels": prompt.labels,
            "config": prompt.config or {},
            "prompt": prompt.prompt,
        }
        path.write_text(json.dumps(exported, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print(f"{prompt.name}: exportována verze {prompt.version}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Správa promptů v Langfuse.")
    commands = parser.add_subparsers(dest="command", required=True)
    push_parser = commands.add_parser("push", help="nahrát prompt z prompts/ do Langfuse")
    push_parser.add_argument("name")
    push_parser.add_argument("--label", default="staging", choices=["staging", "production"])
    push_parser.add_argument("--message", default=None, help="popis změny")
    promote_parser = commands.add_parser("promote", help="dát verzi štítek production")
    promote_parser.add_argument("name")
    promote_parser.add_argument("version", type=int)
    commands.add_parser("export", help="stáhnout prompty se štítkem production do prompts/")
    args = parser.parse_args()

    client = Langfuse()  # klíče a adresa z prostředí (LANGFUSE_*)
    if args.command == "push":
        push(client, args.name, args.label, args.message)
    elif args.command == "promote":
        promote(client, args.name, args.version)
    else:
        export(client)


if __name__ == "__main__":
    main()
