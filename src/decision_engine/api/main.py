"""Vstupní bod `uv run decision-engine`: spustí API i sestavený frontend jedním příkazem."""

import argparse
from pathlib import Path

import uvicorn

from decision_engine.api.app import create_app

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_STATIC_DIR = _REPO_ROOT / "frontend" / "build"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="decision-engine",
        description="Spustí DecisionEngine lokálně (API a sestavený frontend).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="adresa serveru (výchozí 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port serveru (výchozí 8000)")
    parser.add_argument(
        "--static-dir",
        type=Path,
        default=_DEFAULT_STATIC_DIR,
        help="složka sestaveného frontendu (výchozí frontend/build)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Spustí server uvicorn s aplikací DecisionEngine."""
    args = _parse_args(argv)
    host: str = args.host
    port: int = args.port
    static_dir: Path = args.static_dir
    if not (static_dir / "index.html").is_file():
        print(f"Frontend není sestavený ({static_dir}); běží jen API. Spusťte `pnpm build`.")
    print(f"DecisionEngine běží na http://{host}:{port}")
    uvicorn.run(create_app(static_dir), host=host, port=port)


if __name__ == "__main__":
    main()
