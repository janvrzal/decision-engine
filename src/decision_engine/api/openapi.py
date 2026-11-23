"""Export schématu OpenAPI bez spuštěného serveru; zdroj typů pro `pnpm generate:api`."""

import json
import sys
from pathlib import Path
from typing import Any

from decision_engine.api.app import create_app


def openapi_schema() -> dict[str, Any]:
    """Vrátí schéma OpenAPI aplikace."""
    return create_app(static_dir=None).openapi()


def main(argv: list[str] | None = None) -> None:
    """Zapíše schéma do souboru zadaného prvním argumentem."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("Použití: python -m decision_engine.api.openapi <výstupní soubor>")
    output = Path(args[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(openapi_schema(), ensure_ascii=False, indent=2) + "\n"
    output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
