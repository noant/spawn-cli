# Step 1: Junie adapter module, finalize, registration

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Add full `JunieAdapter` in `src/spawn_cli/ide/junie.py`, `finalize_junie_repo` in `src/spawn_cli/ide/_vacancy.py`, and register the `junie` key.

## Approach
Mirror `cursor.py` structure. Order: vacancy helper -> adapter module -> `low_level.py` tuple -> `__init__.py` import/export. `register()` validates the key, so the tuple edit and module import must land in the same step.

## Affected files
- `src/spawn_cli/ide/junie.py` — NEW: `JunieAdapter`, `_build_mcp_server_entry`
- `src/spawn_cli/ide/_vacancy.py` — NEW: `finalize_junie_repo` (+ `__all__` entry)
- `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` append `"junie"`
- `src/spawn_cli/ide/__init__.py` — import + export `JunieAdapter`

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` gains `junie`

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
    "opencode",
    "mimo-code",
    "hermes",
)
```
Canonical IDE key tuple (current tree state, including uncommitted task 29/30 appends); `register()` rejects keys outside it.

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
    "mimo-code",
    "hermes",
    "junie",
)
```
Appends `junie` after the current last entry (append-only convention; `tests/ide/test_registry.py` asserts order). NOTE: the tree may contain uncommitted appends from concurrent tasks (mimo-code, hermes) — re-check the current tuple with `git diff src/spawn_cli/core/low_level.py` before editing and append `junie` at the end without touching other entries.

### `src/spawn_cli/ide/__init__.py` — import and export

**Before**
```python
from . import cline  # noqa: F401
from . import opencode  # noqa: F401
from . import mimo_code  # noqa: F401
from . import hermes  # noqa: F401
```
Adapter module imports (registration side effects at import time; current tree includes uncommitted task 29/30 modules).

**After**
```python
from . import cline  # noqa: F401
from . import opencode  # noqa: F401
from . import mimo_code  # noqa: F401
from . import hermes  # noqa: F401
from . import junie  # noqa: F401
```
Imports the new adapter module after `hermes` (append position; never reorder or disturb concurrent-task entries) so `register(JunieAdapter())` runs.

**Before**
```python
from .cline import ClineAdapter
from .opencode import OpenCodeAdapter
from .mimo_code import MimoCodeAdapter
from .hermes import HermesAdapter
```
Concrete adapter re-exports.

**After**
```python
from .cline import ClineAdapter
from .opencode import OpenCodeAdapter
from .mimo_code import MimoCodeAdapter
from .hermes import HermesAdapter
from .junie import JunieAdapter
```
Exposes `JunieAdapter` after `HermesAdapter`.

**Before**
```python
__all__ = [
    "ALIASES",
    "ClineAdapter",
    "OpenCodeAdapter",
    "MimoCodeAdapter",
    "HermesAdapter",
```
Public names list (not sorted; append in the same position as the re-export).

**After**
```python
__all__ = [
    "ALIASES",
    "ClineAdapter",
    "OpenCodeAdapter",
    "MimoCodeAdapter",
    "HermesAdapter",
    "JunieAdapter",
```
Adds `JunieAdapter` to `__all__` right after `HermesAdapter`.

### `src/spawn_cli/ide/junie.py` — NEW full adapter

**Before**
(insertion context: no `junie.py` exists; `get("junie")` raises `SpawnError` from `registry.get`)

**After**
```python
"""JetBrains Junie IDE adapter: .junie/skills, .junie/mcp/mcp.json, .aiignore, AGENTS.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.errors import SpawnWarning
from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.ide._helpers import (
    clear_split_agent_ignore_file,
    remove_ignore_block,
    rewrite_core_agent_ignore_region,
    rewrite_extension_agent_ignore_region,
    rewrite_ignore_block,
)
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    register,
    normalize_skill_name,
    render_skill_md,
    rewrite_managed_block,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


def _build_mcp_server_entry(server: McpServer) -> dict:
    """Convert McpServer to .junie/mcp/mcp.json entry (mcpServers format)."""
    transport = server.transport
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            entry = {"command": "spawn", "args": mcp_stdio_argv(server.extension, server.name)}
        else:
            entry = {"command": transport.command, "args": transport.args}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": transport.type, "url": transport.url}
        if transport.headers:
            entry["headers"] = {k: f"${{{v}}}" for k, v in transport.headers.items()}
    else:
        entry = {"command": transport.command, "args": transport.args}
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else v.value or f"${{{k}}}"
            for k, v in server.env.items()
        }
    return entry


class JunieAdapter(IdeAdapter):
    key = "junie"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".junie").exists()
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
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".junie" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}", SpawnWarning)
            skill_path.write_text(render_skill_md(skill.model_copy(update={"name": name})), encoding="utf-8")
            rel = skill_path.relative_to(target_root).as_posix()
            results.append({"skill": skill.name, "path": rel})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        """Merge Spawn-owned servers into .junie/mcp/mcp.json (mcpServers format)."""
        mcp_path = target_root / ".junie" / "mcp" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            entry = _build_mcp_server_entry(server)
            data["mcpServers"][server.name] = entry
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        """Remove named entries from .junie/mcp/mcp.json."""
        mcp_path = target_root / ".junie" / "mcp" / "mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".aiignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".aiignore", globs)

    def rewrite_core_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_core_agent_ignore_region(target_root / ".aiignore", globs)

    def rewrite_extension_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_extension_agent_ignore_region(target_root / ".aiignore", globs)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        clear_split_agent_ignore_file(target_root / ".aiignore")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_junie_repo(target_root)


register(JunieAdapter())

__all__ = ["JunieAdapter"]
```
Full adapter: native skills in `.junie/skills/<name>/SKILL.md` (frontmatter `name` forced to the normalized dir name via `model_copy`, cline/opencode rule 04 pattern), project MCP at `.junie/mcp/mcp.json`, `.aiignore` managed block, AGENTS.md entry point; user-facing warnings use `SpawnWarning` (rule 03); registered at import.

### `src/spawn_cli/ide/_vacancy.py` — NEW `finalize_junie_repo`

**Before**
```python
def finalize_cline_repo(target_root: Path) -> None:
```
Vacancy finalizers live here; junie has none.

**After**
```python
def finalize_junie_repo(target_root: Path) -> None:
    """Junie adapter: `.junie/{skills,mcp/mcp.json}`; drop parts when vacant, keep user content."""
    junie_root = target_root / ".junie"
    if not junie_root.is_dir():
        return
    try_unlink_empty_mcp_mcp_servers(junie_root / "mcp" / "mcp.json")
    prune_empty_directories_under(junie_root)
    if ide_dotdir_is_entirely_removable(junie_root, allow_delete_entire=True):
        shutil.rmtree(junie_root, ignore_errors=True)
    ignore = target_root / ".aiignore"
    if ignore.is_file():
        clear_split_agent_ignore_file(ignore)
        if not ignore.read_text(encoding="utf-8").strip():
            ignore.unlink(missing_ok=True)


def finalize_cline_repo(target_root: Path) -> None:
```
Removes Spawn-owned Junie artifacts when vacant; `.junie` is deleted only when it contains zero files (user content like `memory/` or `rules/` prevents removal).

**Before**
```python
__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_cline_repo",
    "finalize_hermes_repo",
    "finalize_mimo_code_repo",
    "finalize_opencode_repo",
```
Vacancy finalizer exports (current tree includes uncommitted task 29/30 entries).

**After**
```python
__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_cline_repo",
    "finalize_hermes_repo",
    "finalize_junie_repo",
    "finalize_mimo_code_repo",
    "finalize_opencode_repo",
```
Exports the new `finalize_junie_repo` (alphabetical insert among `finalize_*` rows).

## Additional actions
- After implementation: `python -c "import spawn_cli.ide as m; print(m.get('junie').key)"` must print `junie`.
