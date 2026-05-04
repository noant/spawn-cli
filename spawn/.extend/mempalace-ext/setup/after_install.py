"""Spawn after-install: pinned pip install + interactive ``mempalace init`` in the target repo.

Runs in the consumer repository (Spawn should use the target root as cwd):

1. ``pip install`` or, if ``pip`` is missing, ``uv pip install --python=...`` unless skipped.
2. ``mempalace init .`` unless skipped — scaffold project palace files. Stdin/stdout/stderr
   are inherited so prompts (entities, mine, etc.) work when Spawn forwards hook I/O.

   Set ``MEMPALACE_EXTENSION_AUTO_MINE`` to pass ``--auto-mine`` (long-running,
   skips the usual mine confirmation flow).

Update ``MEMPALACE_PYPI_VERSION`` when this extension adopts a newer supported release.

Environment:

- ``MEMPALACE_EXTENSION_SKIP_PIP`` = ``1`` / ``true`` / ``yes`` — skip pip (init still runs if not skipped).
- ``MEMPALACE_EXTENSION_SKIP_INIT`` = ``1`` / ``true`` / ``yes`` — skip ``mempalace init``.
- ``MEMPALACE_EXTENSION_AUTO_MINE`` = ``1`` / ``true`` / ``yes`` — pass ``--auto-mine`` to ``init`` so mining runs immediately (no prompt; long-running).
- ``MEMPALACE_EXTENSION_GLOBAL_PALACE`` = ``1`` / ``true`` / ``yes`` — do **not** force a repo-local palace; keep MemPalace defaults (``~/.mempalace/palace`` unless you already exported ``MEMPALACE_PALACE_PATH``).

If the Spawn CLI Python has no ``pip`` module (typical of some uv-managed installs),
installation falls back to ``uv pip install --python=<that interpreter>`` when ``uv`` is on ``PATH``.

Child processes inherit ``PYTHONUTF8=1`` and ``PYTHONIOENCODING=utf-8`` when unset so
``mempalace init`` (git log via ``text=True`` pipes) does not fail on Windows cp1252.

``pip``/``uv`` subprocess output is captured as UTF-8 and re-printed using ASCII-safe
bytes so a parent process (e.g. Spawn) that decodes hooked stderr as cp1252 does not hit
``UnicodeDecodeError``. The ``mempalace init`` subprocess inherits stdio (no capture).
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Pin must match a version published on https://pypi.org/project/mempalace/
MEMPALACE_PYPI_VERSION = "3.3.4"


def _ascii_safe(s: str) -> str:
    """ASCII-only text so hosting CLIs that decode hooked stderr as cp1252 do not crash."""
    if not s:
        return ""
    return s.encode("ascii", "replace").decode("ascii")


def _err(msg: str) -> None:
    """Stderr with flush so non-TTY Spawn pipes show progress instead of looking hung."""
    print(_ascii_safe(msg), file=sys.stderr, flush=True)


def _run_child(
    cmd: list[str],
    *,
    env: dict[str, str],
    cwd: str | None = None,
    inherit_stdio: bool = False,
) -> None:
    """Run a command.

    By default captures UTF-8 output and forwards as ASCII-safe (avoids host cp1252 decode errors).
    With ``inherit_stdio=True``, attaches to the parent's stdin/stdout/stderr so interactive CLIs work.
    """
    if inherit_stdio:
        r = subprocess.run(cmd, env=env, cwd=cwd)
        if r.returncode != 0:
            raise subprocess.CalledProcessError(r.returncode, cmd, output=None, stderr=None)
        return

    r = subprocess.run(
        cmd,
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.stderr:
        for line in r.stderr.splitlines():
            print(_ascii_safe(line), file=sys.stderr, flush=True)
    if r.stdout:
        for line in r.stdout.splitlines():
            print(_ascii_safe(line), file=sys.stderr, flush=True)
    if r.returncode != 0:
        raise subprocess.CalledProcessError(
            r.returncode,
            cmd,
            output=r.stdout,
            stderr=r.stderr,
        )
def _subprocess_env() -> dict[str, str]:
    """Environment for pip/uv/mempalace subprocesses.

    MemPalace ``init`` runs ``git`` with ``subprocess.run(..., text=True)``. On Windows,
    locale decoding (e.g. cp1252) can choke on UTF-8 in commit metadata and break
    ``mempalace init``. UTF-8 mode keeps those pipes decodable.
    """
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _truthy_env(name: str) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes")


def _skip_pip() -> bool:
    return _truthy_env("MEMPALACE_EXTENSION_SKIP_PIP")


def _skip_init() -> bool:
    return _truthy_env("MEMPALACE_EXTENSION_SKIP_INIT")


def _auto_mine() -> bool:
    return _truthy_env("MEMPALACE_EXTENSION_AUTO_MINE")


def _force_global_default_palace() -> bool:
    """Use MemPalace default palace path (~/.mempalace/palace) instead of repo-local."""
    return _truthy_env("MEMPALACE_EXTENSION_GLOBAL_PALACE")


def _env_for_mempalace_child(root: Path) -> dict[str, str]:
    """Spawn child env UTF-8 + optional repo-local ``MEMPALACE_PALACE_PATH``."""
    env = _subprocess_env()
    if _force_global_default_palace():
        _err(
            "mempalace extension: repo-local palace override disabled "
            "(MEMPALACE_EXTENSION_GLOBAL_PALACE)",
        )
        return env

    inherits = (
        (env.get("MEMPALACE_PALACE_PATH") or "").strip()
        or (env.get("MEMPAL_PALACE_PATH") or "").strip()
    )
    if inherits:
        _err(
            "mempalace extension: keeping inherited "
            "MEMPALACE_PALACE_PATH / MEMPAL_PALACE_PATH for init",
        )
        return env

    palace = str((root / ".mempalace" / "palace").resolve())
    env["MEMPALACE_PALACE_PATH"] = palace
    _err(f"mempalace extension: MEMPALACE_PALACE_PATH={_ascii_safe(palace)} (repo-local default)")
    return env


def _mempalace_cli() -> list[str]:
    """Resolve the mempalace CLI next to this Python (venv Scripts / bin)."""
    d = Path(sys.executable).resolve().parent
    for name in ("mempalace.exe", "mempalace"):
        p = d / name
        if p.exists():
            return [str(p)]
    return [sys.executable, "-m", "mempalace"]


def _install_mempalace_pip(spec: str) -> int:
    """Install mempalace into the same environment as ``sys.executable``.

    Prefer ``python -m pip`` when the ``pip`` module exists; otherwise use
    ``uv pip install --python=...`` if ``uv`` is available (covers uv-managed
    interpreters without pip).
    """
    if importlib.util.find_spec("pip") is not None:
        cmd = [sys.executable, "-m", "pip", "install", spec]
        _err("mempalace extension: " + " ".join(cmd))
        try:
            _run_child(cmd, env=_subprocess_env())
        except subprocess.CalledProcessError as e:
            _err(
                f"mempalace extension: pip install failed; install manually, e.g. pip install {spec}",
            )
            return int(e.returncode) if e.returncode is not None else 1
        return 0

    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "pip", "install", f"--python={sys.executable}", spec]
        _err("mempalace extension: " + " ".join(cmd))
        try:
            _run_child(cmd, env=_subprocess_env())
        except subprocess.CalledProcessError as e:
            _err(
                "mempalace extension: uv pip install failed; install manually, e.g. "
                f"uv pip install --python={sys.executable} {spec}",
            )
            return int(e.returncode) if e.returncode is not None else 1
        return 0

    _err(
        "mempalace extension: no pip module on this Python and `uv` not found on PATH; "
        f"install manually, e.g. uv pip install --python={sys.executable} {spec}",
    )
    return 1


def main() -> int:
    _err(
        "mempalace extension: after_install starting "
        "(pip/uv logs are buffered; mempalace init is interactive via inherited stdio).",
    )
    if _skip_pip():
        _err(
            "mempalace extension: skipping pip install (MEMPALACE_EXTENSION_SKIP_PIP set)",
        )
    else:
        spec = f"mempalace=={MEMPALACE_PYPI_VERSION}"
        rc = _install_mempalace_pip(spec)
        if rc != 0:
            return rc
        _err("mempalace extension: package install step finished.")

    if _skip_init():
        _err(
            "mempalace extension: skipping mempalace init (MEMPALACE_EXTENSION_SKIP_INIT set)",
        )
        return 0

    root = Path.cwd().resolve()
    auto_mine = _auto_mine()
    init_cmd = _mempalace_cli() + ["init", "."]
    if auto_mine:
        init_cmd.append("--auto-mine")
    _err(
        "mempalace extension: " + " ".join(init_cmd) + f" (cwd={root})",
    )
    if auto_mine:
        _err(
            "mempalace extension: --auto-mine enabled; first mine may take a long time.",
        )
    try:
        _run_child(
            init_cmd,
            cwd=str(root),
            env=_env_for_mempalace_child(root),
            inherit_stdio=True,
        )
    except subprocess.CalledProcessError as e:
        _err(
            "mempalace extension: mempalace init failed; run manually from repo root: "
            "mempalace init .",
        )
        return int(e.returncode) if e.returncode is not None else 1

    _err("mempalace extension: after_install finished successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
