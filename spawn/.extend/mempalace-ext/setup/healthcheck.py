"""Spawn healthcheck: verify ``mempalace`` and Chroma backend imports in the current Python."""

from __future__ import annotations

import sys


def _emit(msg: str) -> None:
    # Spawn and some tooling surface stdout more reliably than stderr; mirror both streams.
    print(msg, flush=True)
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    try:
        import mempalace  # noqa: F401
        from mempalace.backends import chroma  # noqa: F401
    except ImportError as exc:
        _emit(
            "mempalace healthcheck: import failed (mine/MCP need Chroma deps). "
            f"{exc}. Install pinned deps from .mempalace/ext/requirements-mempalace.txt "
            f"(includes attrs>=22.2.0 for jsonschema). "
            f"Interpreter:\n  {sys.executable}",
        )
        return 1
    except Exception as exc:  # pragma: no cover - defensive against broken partial installs
        _emit(
            f"mempalace healthcheck: import raised {type(exc).__name__}: {exc}. "
            f"Install pinned deps from .mempalace/ext/requirements-mempalace.txt "
            f"(includes attrs>=22.2.0 for jsonschema). "
            f"Interpreter:\n  {sys.executable}",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
