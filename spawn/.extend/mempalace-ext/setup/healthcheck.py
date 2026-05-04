"""Spawn healthcheck: verify ``mempalace`` is importable in the current Python."""

from __future__ import annotations

import sys


def _emit(msg: str) -> None:
    # Spawn and some tooling surface stdout more reliably than stderr; mirror both streams.
    print(msg, flush=True)
    print(msg, file=sys.stderr, flush=True)


def main() -> int:
    try:
        import mempalace  # noqa: F401
    except ImportError:
        _emit(
            "mempalace healthcheck: cannot import mempalace in this interpreter. "
            "Install pinned deps from .mempalace/ext/requirements-mempalace.txt "
            "(or pip install mempalace). "
            f"Interpreter:\n  {sys.executable}",
        )
        return 1
    except Exception as exc:  # pragma: no cover - defensive against broken partial installs
        _emit(
            f"mempalace healthcheck: import raised {type(exc).__name__}: {exc}. "
            f"Interpreter:\n  {sys.executable}",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
