# Step 2: Mimo Code adapter module and vacancy pruner

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Create the full `MimoCodeAdapter` at `src/spawn_cli/ide/mimo_code.py` and its vacancy pruner `finalize_mimo_code_repo` in `_vacancy.py`, mirroring the OpenCode adapter.

## Approach
Copy the `opencode.py` structure (config-based adapter family) with MiMo-specific paths: `.mimocode/mimocode.json` canonical config, `.mimocode/skills/`, `AGENTS.md` entry point, `permission.read/edit` deny globs. Honor rules 01, 02, 03, 05; rule 04 not needed (MiMo reads the skill name from frontmatter).

## Affected files
- `src/spawn_cli/ide/mimo_code.py` — new module: `MimoCodeAdapter`, `_CONFIG`, `_load_config`, `_save_config`, `_build_mcp_entry`, `register(MimoCodeAdapter())`
- `src/spawn_cli/ide/_vacancy.py` — `finalize_mimo_code_repo`, `__all__`

## Code changes (before / after)

### `src/spawn_cli/ide/mimo_code.py` — new module (insertion context: none exists today)

**Before**
```python
# (no such file; grep confirms "mimo" absent from src/)
```
MiMo Code is unsupported; the seed asks for a full adapter replacing the nonexistent stub.

**After**
```python
"""Mimo Code adapter: .mimocode/skills, .mimocode/mimocode.json (mcp + permission), AGENTS.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import _vacancy as _vac
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

_CONFIG = Path(".mimocode") / "mimocode.json"


def _load_config(target_root: Path) -> dict:
    path = target_root / _CONFIG
    if not path.exists():
        if (target_root / ".mimocode" / "mimocode.jsonc").exists():
            warnings.warn(
                "Mimo Code: Spawn manages .mimocode/mimocode.json; existing mimocode.jsonc is not merged",
                SpawnWarning,
            )
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpawnError(f"Mimo Code config is not valid JSON: {path} ({exc})") from exc


def _save_config(target_root: Path, data: dict) -> None:
    path = target_root / _CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _build_mcp_entry(server: McpServer) -> dict:
    # identical semantics to opencode._build_mcp_entry (lines 55-75): local/remote
    # entries, spawn stdio proxy via mcp_stdio_argv, {env:K} placeholders for
    # header values, `environment` key for server.env, enabled=True
    ...


class MimoCodeAdapter(IdeAdapter):
    key = "mimo-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".mimocode").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="project",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root, skill_metadata): ...
    def remove_skills(self, target_root, rendered_paths): ...
    def add_mcp(self, target_root, normalized_mcp): ...
    def remove_mcp(self, target_root, rendered_mcp_names): ...
    def add_agent_ignore(self, target_root, globs): ...
    def remove_agent_ignore(self, target_root, globs): ...
    def clear_spawn_agent_ignore(self, target_root): ...
    def rewrite_entry_point(self, target_root, prompt): ...
    def finalize_repo_after_ide_removed(self, target_root): ...


register(MimoCodeAdapter())

__all__ = ["MimoCodeAdapter"]
```
Full adapter mirroring `opencode.py`: skills at `.mimocode/skills/<normalize_skill_name(name)>/SKILL.md` (SpawnWarning on overwrite, frontmatter name == dirname); MCP under config key `mcp` (local stdio/proxy -> `{"type":"local","command":[...]}`, remote -> `{"type":"remote","url":...,"headers":...}`, `enabled: true`); agent ignore as `permission.read`/`permission.edit` glob -> `"deny"` with empty-subtree pruning; `clear_spawn_agent_ignore` via `ll.get_agent_ignore_list(target_root, self.key)`; entry point root `AGENTS.md` via `rewrite_managed_block`; `finalize_repo_after_ide_removed` -> `_vac.finalize_mimo_code_repo`.

### `src/spawn_cli/ide/_vacancy.py` — new pruner (after `finalize_cline_repo`, before `__all__`)

**Before**
```python
__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_cline_repo",
    "finalize_opencode_repo",
    "finalize_codex_repo",
    "finalize_github_copilot_repo",
    "finalize_standard_dotdir_skills_and_mcp",
    "ide_dotdir_is_entirely_removable",
    "json_value_nonempty",
    "mcp_json_mcp_servers_format_is_empty",
    "prune_empty_directories_under",
    "vscode_servers_mcp_json_is_empty",
]
```
Vacancy pruners exist for every config-writing adapter; Mimo has none, so spawn-written `.mimocode` subtrees would survive IDE removal (rule 01 violation).

**After**
```python
def _mimo_config_vacant(path: Path) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return False  # user config in an unexpected shape: keep untouched
    if data == {}:
        return True
    for key, value in data.items():
        if key in ("mcp", "permission"):
            if value:  # non-empty -> user content or live servers
                return False
        elif json_value_nonempty(value):  # unknown user key with substance
            return False
    return True


def finalize_mimo_code_repo(target_root: Path) -> None:
    """Mimo Code adapter: `.mimocode/mimocode.json` (keys mcp, permission) and `.mimocode/skills`; drop when vacant."""
    config = target_root / ".mimocode" / "mimocode.json"
    if config.is_file():
        try:
            vacant = _mimo_config_vacant(config)
        except json.JSONDecodeError:
            vacant = False  # keep unparseable user config untouched
        if vacant:
            config.unlink()
    skills_dir = target_root / ".mimocode" / "skills"
    if skills_dir.is_dir() and not dir_has_any_file(skills_dir):
        prune_empty_directories_under(target_root / ".mimocode")
    if (target_root / ".mimocode").is_dir() and not dir_has_any_file(target_root / ".mimocode"):
        (target_root / ".mimocode").rmdir()


__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_cline_repo",
    "finalize_mimo_code_repo",
    "finalize_opencode_repo",
    "finalize_codex_repo",
    "finalize_github_copilot_repo",
    "finalize_standard_dotdir_skills_and_mcp",
    "ide_dotdir_is_entirely_removable",
    "json_value_nonempty",
    "mcp_json_mcp_servers_format_is_empty",
    "prune_empty_directories_under",
    "vscode_servers_mcp_json_is_empty",
]
```
Mirrors `finalize_opencode_repo` (line 247): `_mimo_config_vacant` checks the known spawn keys `mcp` / `permission` are absent/empty and no substantive user keys remain; removes the canonical config when spawn-only and vacant, prunes empty `.mimocode` trees; unparseable configs are left untouched.

## Additional actions
None.
