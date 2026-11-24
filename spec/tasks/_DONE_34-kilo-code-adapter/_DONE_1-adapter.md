# Step 1: Kilo Code adapter module and wiring

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Create `KiloCodeAdapter` with skills/MCP/ignore/entry-point support and wire it into the registry, canonical keys, exports, aliases, and vacancy pruner.

## Approach
Follow `spawn/rules/06-new-ide-adapter-checklist.md` items 1-8. MCP mechanics copied from `src/spawn_cli/ide/mimo_code.py`; text-ignore mechanics from `src/spawn_cli/ide/cline.py`; skill-name sanitization from `src/spawn_cli/ide/opencode.py` (`_sanitize_skill_name`). Warnings via `SpawnWarning`, config errors via `SpawnError` (rules 03, 05).

## Affected files
- `src/spawn_cli/core/low_level.py` - `CANONICAL_IDE_KEYS`
- `src/spawn_cli/ide/kilo_code.py` - new module: `KiloCodeAdapter`, `_load_config`, `_save_config`, `_build_mcp_entry`, `_sanitize_skill_name`
- `src/spawn_cli/ide/registry.py` - `ALIASES`
- `src/spawn_cli/ide/__init__.py` - import + re-export + `__all__`
- `src/spawn_cli/ide/_vacancy.py` - `finalize_kilo_code_repo` + `__all__`

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS`
**Before**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    ...
    "junie",
)
```
**After**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    ...
    "junie",
    "kilo-code",
)
```
Append-only: `register()` raises `SpawnError` for keys missing from the constant.

### `src/spawn_cli/ide/kilo_code.py` — new `KiloCodeAdapter`
**Before**
(no file)
**After**
```python
"""Kilo Code adapter: .kilo/skills, .kilo/kilo.json (mcp), .kilocodeignore, AGENTS.md."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide._helpers import (
    clear_split_agent_ignore_file,
    remove_ignore_block,
    rewrite_core_agent_ignore_region,
    rewrite_extension_agent_ignore_region,
    rewrite_ignore_block,
    rewrite_managed_block,
)
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    normalize_skill_name,
    register,
    render_skill_md,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata

_CONFIG = Path(".kilo") / "kilo.json"


def _sanitize_skill_name(name: str) -> str:
    # Kilo: name regex ^[a-z0-9]+(-[a-z0-9]+)*$, max 64 chars (rule 04).
    name = normalize_skill_name(name)
    name = name.replace("_", "-").replace(".", "-")
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return name[:64].strip("-")


def _load_config(target_root: Path) -> dict:
    path = target_root / _CONFIG
    if not path.exists():
        variants = []
        if (target_root / ".kilo" / "kilo.jsonc").exists():
            variants.append(".kilo/kilo.jsonc")
        if (target_root / "kilo.json").exists():
            variants.append("kilo.json")
        if (target_root / "kilo.jsonc").exists():
            variants.append("kilo.jsonc")
        if variants:
            warnings.warn(
                "Kilo Code: Spawn manages .kilo/kilo.json; existing "
                + ", ".join(variants)
                + " not merged",
                SpawnWarning,
            )
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpawnError(f"Kilo Code config is not valid JSON: {path} ({exc})") from exc


def _save_config(target_root: Path, data: dict) -> None:
    path = target_root / _CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _build_mcp_entry(server: McpServer) -> dict:
    # Same local/remote shape as Mimo Code (OpenCode family); Kilo reads the
    # top-level "mcp" key of kilo.json with {env:VAR} placeholders.
    transport = server.transport
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            entry = {
                "type": "local",
                "command": ["spawn"] + mcp_stdio_argv(server.extension, server.name),
            }
        else:
            entry = {"type": "local", "command": [transport.command, *list(transport.args)]}
    else:
        entry = {"type": "remote", "url": transport.url}
        if transport.headers:
            entry["headers"] = {k: f"{{env:{v}}}" for k, v in transport.headers.items()}
    entry["enabled"] = True
    if server.env:
        entry["environment"] = {
            k: f"{{env:{k}}}" if v.secret else (v.value or f"{{env:{k}}}")
            for k, v in server.env.items()
        }
    return entry


class KiloCodeAdapter(IdeAdapter):
    key = "kilo-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (
            (target_root / ".kilo").exists()
            or (target_root / ".kilocode").exists()
            or (target_root / "kilo.json").exists()
            or (target_root / "kilo.jsonc").exists()
        )
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="native",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = _sanitize_skill_name(skill.name)
            skill_dir = target_root / ".kilo" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}", SpawnWarning)
            # Kilo requires frontmatter name == directory name.
            rendered = render_skill_md(skill.model_copy(update={"name": name}), "AGENTS.md")
            skill_path.write_text(rendered, encoding="utf-8")
            results.append({"skill": skill.name, "path": skill_path.relative_to(target_root).as_posix()})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        data = _load_config(target_root)
        mcp = data.setdefault("mcp", {})
        for server in normalized_mcp.servers:
            mcp[server.name] = _build_mcp_entry(server)
        _save_config(target_root, data)
        return [s.name for s in normalized_mcp.servers]

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        if not (target_root / _CONFIG).exists():
            return
        data = _load_config(target_root)
        mcp = data.get("mcp")
        if isinstance(mcp, dict):
            for name in rendered_mcp_names:
                mcp.pop(name, None)
            if not mcp:
                data.pop("mcp", None)
        _save_config(target_root, data)

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".kilocodeignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".kilocodeignore", globs)

    def rewrite_core_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_core_agent_ignore_region(target_root / ".kilocodeignore", globs)

    def rewrite_extension_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_extension_agent_ignore_region(target_root / ".kilocodeignore", globs)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        clear_split_agent_ignore_file(target_root / ".kilocodeignore")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_kilo_code_repo(target_root)


register(KiloCodeAdapter())

__all__ = ["KiloCodeAdapter"]
```
Adapters render skills/MCP/ignore/entry point; `spawn ide add/remove kilo-code` becomes functional once wired.

### `src/spawn_cli/ide/registry.py` — `ALIASES`
**Before**
```python
    "mimo": "mimo-code",
}
```
**After**
```python
    "mimo": "mimo-code",
    "kilo": "kilo-code",
}
```
Short CLI alias for the multi-word canonical key (checklist item 4).

### `src/spawn_cli/ide/__init__.py` — wiring
**Before**
```python
from . import junie  # noqa: F401
from ._stub import StubAdapter
```
**After**
```python
from . import junie  # noqa: F401
from . import kilo_code  # noqa: F401
from ._stub import StubAdapter
```
Plus class import `from .kilo_code import KiloCodeAdapter` (after `from .junie import JunieAdapter`) and `"KiloCodeAdapter",` in `__all__` (checklist item 3).

### `src/spawn_cli/ide/_vacancy.py` — `finalize_kilo_code_repo`
**Before**
(no function; `__all__` lacks the name)
**After**
```python
def _kilo_config_vacant(path: Path) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return False  # user config in an unexpected shape: keep untouched
    if data == {}:
        return True
    for key, value in data.items():
        if key in ("mcp",):
            if value:
                return False
        elif json_value_nonempty(value):
            return False
    return True


def finalize_kilo_code_repo(target_root: Path) -> None:
    """Kilo Code adapter: `.kilo/kilo.json` (key mcp), `.kilo/skills`, legacy `.kilocode/`, root `.kilocodeignore`; drop when vacant."""
    config = target_root / ".kilo" / "kilo.json"
    if config.is_file():
        try:
            vacant = _kilo_config_vacant(config)
        except json.JSONDecodeError:
            vacant = False  # keep unparseable user config untouched
        if vacant:
            config.unlink()
    for dotdir in (".kilo", ".kilocode"):
        # .kilocode is a legacy upstream marker dir; spawn never writes into it —
        # prune only the empty dir, never any user content (rule 01 ownership).
        root = target_root / dotdir
        if root.is_dir():
            prune_empty_directories_under(root)
            if not dir_has_any_file(root):
                root.rmdir()
    ignore = target_root / ".kilocodeignore"
    if ignore.is_file():
        clear_split_agent_ignore_file(ignore)
        if not ignore.read_text(encoding="utf-8").strip():
            ignore.unlink(missing_ok=True)
```
Add `"finalize_kilo_code_repo",` to `__all__` (checklist item 5; rule 01 — the only spawn-written subtrees are `.kilo/kilo.json` key `mcp`, `.kilo/skills`, and the `.kilocodeignore` spawn block).

## Additional actions
Run `uv run pytest tests/ide/test_registry.py -q` after wiring to confirm import and registration.
