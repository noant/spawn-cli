# Step 1: Adapter, registration, tests

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Implement `OpenCodeAdapter` in `src/spawn_cli/ide/opencode.py`, register it (import + `CANONICAL_IDE_KEYS`), and add `tests/ide/test_opencode.py` plus the parity-test param.

## Approach
1. Append `"opencode"` to `CANONICAL_IDE_KEYS` FIRST (registry `register()` validates against it). Registration and the tuple change must land together, otherwise `tests/ide/test_registry.py` fails (`get(key)` raises SpawnError).
2. Implement the adapter per `## Details` of `overview.md` (decisions 1-4, 6, 7).
3. Add import registration in `src/spawn_cli/ide/__init__.py`.
4. Mirror `tests/ide/test_cline.py` / `test_claude_code.py` structure for `tests/ide/test_opencode.py`.
5. Add opencode param to `tests/ide/test_mcp_stdio_proxy_parity.py` reading root `opencode.json` (key `mcp`).
6. Run `python -m pytest tests/ide -x -q` — all green.

## Affected files
- `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS`
- `src/spawn_cli/ide/opencode.py` — NEW: `OpenCodeAdapter`, `_sanitize_skill_name`, `_build_mcp_entry`, `register(OpenCodeAdapter())`
- `src/spawn_cli/ide/__init__.py` — imports and `__all__`
- `tests/ide/test_opencode.py` — NEW
- `tests/ide/test_mcp_stdio_proxy_parity.py` — parametrize list + opencode read branch

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` gains `opencode`
**Before**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
    "cline",
)
```
Canonical IDE key order used by detect/registry iteration; new keys appended at the end (task 27 precedent).
**After**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
    "cline",
    "opencode",
)
```
`opencode` becomes a canonical key so `register(OpenCodeAdapter())` passes validation.

### `src/spawn_cli/ide/opencode.py` — NEW module (whole file)
**Before**
(nothing to quote; insertion context: sibling adapters live at `src/spawn_cli/ide/<key>.py`, each ending with `register(<Adapter>())`)
New file; `opencode` has no adapter today.
**After**
```python
"""OpenCode CLI adapter: .opencode/skills, root opencode.json (mcp + permission), AGENTS.md."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    normalize_skill_name,
    register,
    render_skill_md,
    rewrite_managed_block,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata

_CONFIG = "opencode.json"


def _load_config(target_root: Path) -> dict:
    path = target_root / _CONFIG
    if not path.exists():
        if (target_root / "opencode.jsonc").exists():
            warnings.warn(
                "OpenCode: Spawn manages opencode.json; existing opencode.jsonc is not merged",
                SpawnWarning,
            )
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpawnError(f"OpenCode config is not valid JSON: {path} ({exc})") from exc


def _save_config(target_root: Path, data: dict) -> None:
    (target_root / _CONFIG).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _sanitize_skill_name(name: str) -> str:
    name = normalize_skill_name(name)
    name = name.replace("_", "-").replace(".", "-")
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return name


def _build_mcp_entry(server: McpServer) -> dict:
    transport = server.transport
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            entry = {
                "type": "local",
                "command": ["spawn"] + mcp_stdio_argv(server.extension, server.name),
            }
        else:
            entry = {"type": "local", "command": [transport.command, *list(transport.args)]}
    else:  # streamable-http and sse both render as remote
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


class OpenCodeAdapter(IdeAdapter):
    key = "opencode"

    def detect(self, target_root: Path) -> DetectResult:
        used = (
            (target_root / ".opencode").exists()
            or (target_root / "opencode.json").exists()
            or (target_root / "opencode.jsonc").exists()
        )
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="project",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = _sanitize_skill_name(skill.name)
            skill_dir = target_root / ".opencode" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}", SpawnWarning)
            # OpenCode requires frontmatter name == directory name.
            rendered = render_skill_md(skill.model_copy(update={"name": name}))
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
        data = _load_config(target_root)
        perms = data.setdefault("permission", {})
        for section in ("read", "edit"):
            rules = perms.setdefault(section, {})
            if not isinstance(rules, dict):
                rules = {}
                perms[section] = rules
            for glob in globs:
                rules[glob] = "deny"
        _save_config(target_root, data)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        if not (target_root / _CONFIG).exists():
            return
        data = _load_config(target_root)
        perms = data.get("permission")
        if not isinstance(perms, dict):
            return
        drop = set(globs)
        for section in ("read", "edit"):
            rules = perms.get(section)
            if isinstance(rules, dict):
                for glob in drop:
                    rules.pop(glob, None)
                if not rules:
                    perms.pop(section, None)
        if not perms:
            data.pop("permission", None)
        _save_config(target_root, data)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        recorded = ll.get_agent_ignore_list(target_root, self.key)
        if recorded:
            self.remove_agent_ignore(target_root, recorded)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()


register(OpenCodeAdapter())

__all__ = ["OpenCodeAdapter"]
```
Full adapter: detect via `.opencode` / `opencode.json(c)`; skills under `.opencode/skills/<name>/SKILL.md` with OpenCode-safe names; MCP merged into root `opencode.json` key `mcp` (local argv-array / remote shapes, `{env:VAR}` placeholders); project ignore via `permission.read/edit` deny dicts with spawn-owned-subtree pruning; AGENTS.md managed block.

### `src/spawn_cli/ide/__init__.py` — import registration
**Before**
```python
from . import cline  # noqa: F401
```
Package import side-effect registers all concrete adapters.
**After**
```python
from . import cline  # noqa: F401
from . import opencode  # noqa: F401
```
Registers OpenCodeAdapter at import time.
**Before**
```python
from .cline import ClineAdapter
```
Re-export block.
**After**
```python
from .cline import ClineAdapter
from .opencode import OpenCodeAdapter
```
Exposes the class.
**Before**
```python
    "ClineAdapter",
```
`__all__` entry.
**After**
```python
    "ClineAdapter",
    "OpenCodeAdapter",
```
Public export.

### `tests/ide/test_mcp_stdio_proxy_parity.py` — opencode param
**Before**
```python
        pytest.param(GitHubCopilotAdapter(), "vscode_json", id="github_copilot"),
    ],
)
```
Parameterized golden test over adapters that support the stdio proxy.
**After**
```python
        pytest.param(GitHubCopilotAdapter(), "vscode_json", id="github_copilot"),
        pytest.param(OpenCodeAdapter(), "opencode_json", id="opencode"),
    ],
)
```
Adds opencode; add the `OpenCodeAdapter` import and an `"opencode_json"` read branch (root `opencode.json`, key `mcp`) alongside the existing `read_entries` branches. NOTE: opencode emits a single argv-array (`"command": ["spawn", ...]`, no `"args"` key), so `_assert_stdio_wrapper_golden` needs an opencode branch: assert `proxy_entry["command"] == ["spawn"] + mcp_stdio_argv(extension_id, server_name)` and that `"tool-uv-name"` is not in `proxy_entry["command"]` (peers keep the string `"command": "spawn"` + `"args"` list unchanged).

### `tests/ide/test_opencode.py` — NEW (mirror `tests/ide/test_cline.py` structure)
**Before**
(nothing to quote; insertion context: one test module per adapter under `tests/ide/`)
No tests for opencode.
**After**
```python
"""Tests for the OpenCode CLI adapter."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.ide.opencode import OpenCodeAdapter


@pytest.fixture
def adapter() -> OpenCodeAdapter:
    return OpenCodeAdapter()
```
Then cover (mirroring peers): detect positives (`.opencode/`, `opencode.json`, `opencode.jsonc`) and negative; capabilities values; add_skills writes `.opencode/skills/<name>/SKILL.md`, sanitizes `.`/`_` to `-`, forces frontmatter name == dirname, warns on overwrite (SpawnWarning category); remove_skills deletes file and empty dir; add_mcp creates root `opencode.json` with `mcp` local shape (`command` array, `enabled`, `environment`) and remote shape (`type:"remote"`, `url`, `headers` `{env:VAR}`), merges with existing user keys, secret env renders `{env:VAR}`; remove_mcp removes entries and prunes empty `mcp` key; add/remove agent ignore roundtrip + idempotent re-add, deny written to both `permission.read` and `permission.edit`; remove prunes only spawn entries (user rules kept); clear_spawn_agent_ignore uses recorded list; rewrite_entry_point writes AGENTS.md managed block markers; invalid `opencode.json` raises SpawnError.
Full coverage per peer adapter test suites.

## Additional actions
- Run `python -m pytest tests/ide -q` and the full suite `python -m pytest -q` before finishing.
