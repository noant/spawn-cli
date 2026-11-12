# Step 1: OpenCode Adapter Implementation

## Goal
Implement the correct `OpencodeAdapter` with proper skills subdirectory layout, MCP merging into `opencode.json`, finalization cleanup, and registry wiring.

## Approach
1. Add `"opencode"` to `CANONICAL_IDE_KEYS` in `low_level.py`.
2. Replace incomplete `finalize_opencode_repo` and add `opencode_config_json_mcp_is_empty` in `_vacancy.py`: unlink `opencode.json` when only empty `mcp` (and `$schema`) remain; prune empty skill subdirs under `.opencode/skills/`; remove `.opencode/` when entirely empty.
3. Fix `OpencodeAdapter` in `src/spawn_cli/ide/opencode.py`: rename `OPENSEA_` constants to `OPENCODE_`, switch `add_skills` to subdirectory layout, add parent-dir cleanup in `remove_skills`.
4. Fix `src/spawn_cli/ide/__init__.py`: remove the duplicate `"OpencodeAdapter"` from `__all__`.
5. Write tests in `tests/ide/test_opencode.py`.
6. Update `tests/ide/test_registry.py` to include `OpencodeAdapter`.

### Skills layout
Each skill is a subdirectory under `.opencode/skills/`:
```
.opencode/skills/{name}/SKILL.md
```
`add_skills` returns `{"skill": skill.name, "path": ".opencode/skills/{name}/SKILL.md"}`.
`remove_skills` deletes the SKILL.md and removes the parent dir if empty afterward.

### MCP builder
`_build_opencode_mcp_entry(server)`:
- stdio (incl. proxy): `{"type": "local", "command": [cmd, *args], "enabled": True}`
- streamable-http or sse: `{"type": "remote", "url": ..., "enabled": True}`
- env vars: if `server.env`, add `"env": {k: "${k}" if secret else value or "${k}"}`

`add_mcp` reads/creates `opencode.json`, merges under `"mcp"` key, writes back.
`remove_mcp` removes named entries from `"mcp"` dict.

## Affected files
- `src/spawn_cli/core/low_level.py` — add `"opencode"` to `CANONICAL_IDE_KEYS`
- `src/spawn_cli/ide/_vacancy.py` — add `finalize_opencode_repo`, add vacancy helper `opencode_config_json_mcp_is_empty`, export both
- `src/spawn_cli/ide/opencode.py` — fix `OPENSEA_` constant typo to `OPENCODE_`, fix `add_skills` to subdirectory layout, fix `remove_skills` to prune empty parent dir
- `src/spawn_cli/ide/__init__.py` — remove duplicate `"OpencodeAdapter"` from `__all__`
- `tests/ide/test_opencode.py` — new file: full test coverage
- `tests/ide/test_registry.py` — add `OpencodeAdapter` import, add `get("opencode")` assertions

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — CANONICAL_IDE_KEYS tuple

**Before**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
)
```

**After**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
    "opencode",
)
```

### `src/spawn_cli/ide/_vacancy.py` — replace incomplete `finalize_opencode_repo` with full implementation, add `opencode_config_json_mcp_is_empty`

Note: the current file already has a partial `finalize_opencode_repo` (handles only flat skill files, no `opencode.json` cleanup, no `.opencode/` dir removal) and does NOT yet have `opencode_config_json_mcp_is_empty`.

**Before** (current incomplete state)
```python
def finalize_opencode_repo(target_root: Path) -> None:
    skills_dir = target_root / ".opencode" / "skills"
    if skills_dir.is_dir():
        for p in list(skills_dir.iterdir()):
            if p.is_file():
                p.unlink()
        try:
            if not any(skills_dir.iterdir()):
                skills_dir.rmdir()
        except OSError:
            pass


__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_codex_repo",
    "finalize_github_copilot_repo",
    "finalize_opencode_repo",
    "finalize_standard_dotdir_skills_and_mcp",
    "ide_dotdir_is_entirely_removable",
    "json_value_nonempty",
    "mcp_json_mcp_servers_format_is_empty",
    "prune_empty_directories_under",
    "vscode_servers_mcp_json_is_empty",
]
```

**After** (replace the two items above with)
```python
def opencode_config_json_mcp_is_empty(path: Path) -> bool:
    """True when opencode.json has no MCP servers and only schema metadata besides."""
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    mcp = data.get("mcp")
    if not (mcp in (None, {}) or (isinstance(mcp, dict) and len(mcp) == 0)):
        return False
    for k, v in data.items():
        if k not in ("$schema", "mcp") and json_value_nonempty(v):
            return False
    return True


def finalize_opencode_repo(target_root: Path) -> None:
    if opencode_config_json_mcp_is_empty(target_root / "opencode.json"):
        (target_root / "opencode.json").unlink(missing_ok=True)
    skills_dir = target_root / ".opencode" / "skills"
    if skills_dir.is_dir():
        for skill_subdir in list(skills_dir.iterdir()):
            if skill_subdir.is_dir():
                for f in list(skill_subdir.iterdir()):
                    if f.is_file():
                        f.unlink()
                try:
                    if not any(skill_subdir.iterdir()):
                        skill_subdir.rmdir()
                except OSError:
                    pass
        try:
            if not any(skills_dir.iterdir()):
                skills_dir.rmdir()
        except OSError:
            pass
    opencode_dir = target_root / ".opencode"
    if ide_dotdir_is_entirely_removable(opencode_dir, allow_delete_entire=True):
        shutil.rmtree(opencode_dir, ignore_errors=True)


__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_codex_repo",
    "finalize_github_copilot_repo",
    "finalize_opencode_repo",
    "finalize_standard_dotdir_skills_and_mcp",
    "ide_dotdir_is_entirely_removable",
    "json_value_nonempty",
    "mcp_json_mcp_servers_format_is_empty",
    "opencode_config_json_mcp_is_empty",
    "prune_empty_directories_under",
    "vscode_servers_mcp_json_is_empty",
]
```

### `src/spawn_cli/ide/opencode.py` — fix constant typo, fix skills layout to subdirectory

Note: the file already exists with two bugs:
1. Constants are named `OPENSEA_CONFIG_JSON_FILENAME` / `OPENSEA_CONFIG_SCHEMA_URL` (typo — "OPENSEA" instead of "OPENCODE").
2. `add_skills` writes flat `.opencode/skills/{name}.md` instead of the required subdirectory `.opencode/skills/{name}/SKILL.md`.
3. `remove_skills` does not clean up empty parent dirs (no subdirectory to remove in the flat layout).

**Before** (current buggy state — key excerpts)
```python
OPENSEA_CONFIG_JSON_FILENAME = "opencode.json"
OPENSEA_CONFIG_SCHEMA_URL = "https://opencode.ai/config.json"
```
```python
    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        skills_dir = target_root / ".opencode" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_path = skills_dir / f"{name}.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            skill_path.write_text(render_skill_md(skill), encoding="utf-8")
            rel = skill_path.relative_to(target_root).as_posix()
            results.append({"skill": skill.name, "path": rel})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
```

**After** (full replacement of the file)
```python
"""OpenCode IDE adapter: skills under .opencode/skills/{name}/SKILL.md, MCP in opencode.json, AGENTS.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
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


OPENCODE_CONFIG_JSON_FILENAME = "opencode.json"
OPENCODE_CONFIG_SCHEMA_URL = "https://opencode.ai/config.json"


def _build_opencode_mcp_entry(server: McpServer) -> dict:
    transport = server.transport
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            cmd = ["spawn", *mcp_stdio_argv(server.extension, server.name)]
        else:
            cmd = [transport.command] if transport.command else []
            cmd.extend(transport.args or [])
        entry: dict = {"type": "local", "command": cmd, "enabled": True}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": "remote", "url": transport.url or "", "enabled": True}
    else:
        cmd = [transport.command] if transport.command else []
        cmd.extend(transport.args or [])
        entry = {"type": "local", "command": cmd, "enabled": True}
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else v.value or f"${{{k}}}"
            for k, v in server.env.items()
        }
    return entry


class OpencodeAdapter(IdeAdapter):
    key = "opencode"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".opencode").exists() or (target_root / OPENCODE_CONFIG_JSON_FILENAME).exists()
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
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".opencode" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            skill_path.write_text(render_skill_md(skill), encoding="utf-8")
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
        config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
        existing_schema = OPENCODE_CONFIG_SCHEMA_URL
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            existing_schema = data.get("$schema", OPENCODE_CONFIG_SCHEMA_URL)
        else:
            data = {}
        data.setdefault("$schema", existing_schema)
        mcp_servers = data.setdefault("mcp", {})
        if not isinstance(mcp_servers, dict):
            mcp_servers = {}
            data["mcp"] = mcp_servers
        rendered_names = []
        for server in normalized_mcp.servers:
            mcp_servers[server.name] = _build_opencode_mcp_entry(server)
            rendered_names.append(server.name)
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
        if not config_path.exists():
            return
        data = json.loads(config_path.read_text(encoding="utf-8"))
        mcp_servers = data.get("mcp")
        if isinstance(mcp_servers, dict):
            for name in rendered_mcp_names:
                mcp_servers.pop(name, None)
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            data = {}
        data.setdefault("$schema", OPENCODE_CONFIG_SCHEMA_URL)
        watcher = data.setdefault("watcher", {})
        if not isinstance(watcher, dict):
            watcher = {}
            data["watcher"] = watcher
        ignore_list = watcher.setdefault("ignore", [])
        if not isinstance(ignore_list, list):
            ignore_list = []
            watcher["ignore"] = ignore_list
        existing = set(ignore_list)
        for g in globs:
            if g not in existing:
                ignore_list.append(g)
                existing.add(g)
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
        if not config_path.exists():
            return
        data = json.loads(config_path.read_text(encoding="utf-8"))
        watcher = data.get("watcher")
        if not isinstance(watcher, dict):
            return
        ignore_list = watcher.get("ignore")
        if not isinstance(ignore_list, list):
            return
        drop = {g.strip() for g in globs if g.strip()}
        watcher["ignore"] = [g for g in ignore_list if g not in drop]
        if not watcher["ignore"]:
            del watcher["ignore"]
        if not watcher:
            del data["watcher"]
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_opencode_repo(target_root)


register(OpencodeAdapter())

__all__ = ["OpencodeAdapter"]
```

### `src/spawn_cli/ide/__init__.py` — remove duplicate `"OpencodeAdapter"` from `__all__`

Note: the imports and the first `"OpencodeAdapter"` entry in `__all__` are already present. The only bug is that `"OpencodeAdapter"` appears **twice** in `__all__` (once near the top of the list at line 52, once near the bottom at line 67).

**Before** (current `__all__` with duplicate — relevant excerpt)
```python
__all__ = [
    ...
    "OpencodeAdapter",       # first occurrence (line 52)
    ...
    "WindsurfAdapter",
    "OpencodeAdapter",       # duplicate — remove this one (line 67)
    ...
]
```

**After**
Remove the second `"OpencodeAdapter"` entry so it appears exactly once in `__all__`. No other changes needed.

### `tests/ide/test_opencode.py` — new file

Tests cover:
- `detect` with `.opencode/` dir, with `opencode.json`, with neither
- `detect` capabilities shape
- `add_skills` creates `.opencode/skills/{name}/SKILL.md`
- `add_skills` normalizes name
- `add_skills` warns on overwrite
- `remove_skills` deletes SKILL.md and empty parent dir
- `add_mcp` creates `opencode.json` with correct shape (local/remote/env)
- `add_mcp` preserves existing schema and user content
- `remove_mcp` removes named entries, leaves others
- `add_agent_ignore` merges globs into `watcher.ignore` in `opencode.json`
- `remove_agent_ignore` removes named globs from `watcher.ignore`, cleans up empty entries
- `rewrite_entry_point` creates/updates AGENTS.md with managed block
- `finalize_repo_after_ide_removed` removes skills, empty skill dirs, empty opencode.json, empty .opencode dir

### `tests/ide/test_registry.py` — add opencode lookup

**Before**
(no opencode assertion)

**After**
```python
assert isinstance(get("opencode"), OpencodeAdapter)
assert get("opencode").key == "opencode"
```

## Additional actions
Run tests after implementation: `python -m pytest tests/ide/test_opencode.py tests/ide/test_registry.py -v`
