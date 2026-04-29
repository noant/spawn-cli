# Step 2: Core Low-Level Utility Modules

## Required reading
Before implementing, read:
- `spec/design/utility.md` — Low-Level Modules section: every function name, signature, and semantic
- `spec/design/data-structure.md` — file shapes read and written by these functions

## Goal
Implement all low-level utility functions from `spec/design/utility.md` as a single cohesive `src/spawn_cli/core/low_level.py` module (plus `core/errors.py` for error types).

## Approach
All functions receive `target_root: Path` as their first argument. They use models from `models/` and I/O helpers from `io/`. No business orchestration here — only direct reads and writes to individual files.

## Affected files

```
src/spawn_cli/core/__init__.py
src/spawn_cli/core/errors.py
src/spawn_cli/core/low_level.py
tests/core/test_low_level.py
```

## `core/errors.py`

```python
class SpawnError(Exception):
    """Raised on errors that stop the command before mutation."""

class SpawnWarning(UserWarning):
    """Raised (or printed) for recoverable inconsistencies."""
```

## `core/low_level.py` — function signatures and semantics

```python
from pathlib import Path
from typing import Any
from spawn_cli.models.config import ExtensionConfig, CoreConfig, IdeList
from spawn_cli.models.metadata import RenderedSkillsMeta, RenderedMcpMeta
from spawn_cli.models.navigation import NavigationFile
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.models.skill import SkillRawInfo, SkillFileRef, SkillMetadata

# ── IDE key registry ─────────────────────────────────────────────────────────
SUPPORTED_IDE_KEYS: list[str] = [
    "cursor", "codex", "qoder", "claude-code", "qwen-code",
    "windsurf", "github-copilot", "aider", "zed", "gemini-cli", "devin",
]

def supported_ide_keys() -> list[str]: ...

# ── Extension/IDE lists ───────────────────────────────────────────────────────
def list_extensions(target_root: Path) -> list[str]:
    """Return folder names under spawn/.extend/."""

def list_ides(target_root: Path) -> list[str]:
    """Return IDE names from spawn/.metadata/ide.yaml."""

def add_ide_to_list(target_root: Path, ide: str) -> None:
    """Add IDE to spawn/.metadata/ide.yaml (idempotent)."""

def remove_ide_from_list(target_root: Path, ide: str) -> None:
    """Remove IDE from spawn/.metadata/ide.yaml."""

# ── Extension config readers ─────────────────────────────────────────────────
def _load_ext_config(target_root: Path, extension: str) -> ExtensionConfig: ...

def get_required_read_global(target_root: Path, extension: str) -> list[SkillFileRef]:
    """Files with globalRead: required."""

def get_required_read_global_all(target_root: Path) -> dict[str, list[SkillFileRef]]:
    """All extensions: {ext: [SkillFileRef]}."""

def get_required_read_ext_local(target_root: Path, extension: str) -> list[SkillFileRef]:
    """Files with localRead: required."""

def get_auto_read_global(target_root: Path, extension: str) -> list[SkillFileRef]:
    """Files with globalRead: auto."""

def get_auto_read_global_all(target_root: Path) -> dict[str, list[SkillFileRef]]:
    """All extensions: {ext: [SkillFileRef]}."""

def get_auto_read_local(target_root: Path, extension: str) -> list[SkillFileRef]:
    """Files with localRead: auto."""

def get_folders(target_root: Path, extension: str) -> dict[str, Any]:
    """Return folders section from extension config."""

def get_removable(target_root: Path, extension: str) -> tuple[list[str], list[str]]:
    """Return (static_files, static_folders) from extension config."""

# ── Skills ───────────────────────────────────────────────────────────────────
def list_skills(target_root: Path, extension: str) -> list[Path]:
    """Return .md files under spawn/.extend/{extension}/skills/."""

def get_skill_raw_info(target_root: Path, extension: str, skill_path: Path) -> SkillRawInfo:
    """Parse skill file: extract frontmatter (name, description), strip it from content,
    and read required-read from extension config entry."""

def generate_skills_metadata(target_root: Path, extension: str) -> list[SkillMetadata]:
    """Merge raw skill info with global+local read metadata.
    required = distinct(skill.required_read + local_required + all global_required)
    auto = distinct(local_auto + all global_auto)
    """

# ── MCP ──────────────────────────────────────────────────────────────────────
def list_mcp(target_root: Path, extension: str) -> NormalizedMcp:
    """Parse spawn/.extend/{extension}/mcp.json into NormalizedMcp.
    Injects extension name into each server."""

def get_navigation_metadata(target_root: Path, extension: str) -> dict:
    """Return {required: [SkillFileRef], contextual: [SkillFileRef]}
    from globalRead: required and globalRead: auto files."""

# ── Agent ignore ─────────────────────────────────────────────────────────────
def get_all_agent_ignore(target_root: Path) -> list[str]:
    """Return core agent-ignore globs + all extension agent-ignore globs."""

def get_core_agent_ignore(target_root: Path) -> list[str]:
    """Read agent-ignore from spawn/.core/config.yaml."""

def get_ext_agent_ignore(target_root: Path, extension: str) -> list[str]:
    """Read agent-ignore from extension config."""

def get_ext_git_ignore(target_root: Path, extension: str) -> list[str]:
    """Read git-ignore from extension config."""

# ── Rendered skills metadata ─────────────────────────────────────────────────
def save_skills_rendered(target_root: Path, ide: str, extension: str, skill_paths: list[dict]) -> None:
    """Rewrite extension section in spawn/.metadata/{ide}/rendered-skills.yaml.
    skill_paths is list of {skill: str, path: str}.
    If empty, removes the extension section."""

def get_rendered_skills(target_root: Path, ide: str, extension: str) -> list[dict]:
    """Return rendered skill entries for one extension."""

# ── Rendered MCP metadata ────────────────────────────────────────────────────
def save_mcp_rendered(target_root: Path, ide: str, extension: str, mcp_names: list[str]) -> None:
    """Rewrite extension section in spawn/.metadata/{ide}/rendered-mcp.yaml."""

def get_rendered_mcp(target_root: Path, ide: str, extension: str) -> list[str]:
    """Return rendered MCP server names for one extension."""

# ── Ignore lists (ownership records) ─────────────────────────────────────────
def get_git_ignore_list(target_root: Path) -> list[str]:
    """Read spawn/.metadata/git-ignore.txt."""

def save_git_ignore_list(target_root: Path, items: list[str]) -> None:
    """Replace spawn/.metadata/git-ignore.txt."""

def get_agent_ignore_list(target_root: Path, ide: str) -> list[str]:
    """Read spawn/.metadata/{ide}/agent-ignore.txt."""

def save_agent_ignore_list(target_root: Path, ide: str, items: list[str]) -> None:
    """Replace spawn/.metadata/{ide}/agent-ignore.txt."""

# ── Global .gitignore ────────────────────────────────────────────────────────
def get_global_gitignore(target_root: Path) -> list[str]:
    """Read lines from target repo .gitignore; returns [] if missing."""

def push_to_global_gitignore(target_root: Path, items: list[str]) -> None:
    """Append Spawn-owned items to .gitignore (avoid duplicates)."""

def remove_from_global_gitignore(target_root: Path, items: list[str]) -> None:
    """Remove Spawn-owned items from .gitignore, preserve user lines."""

# ── Navigation ───────────────────────────────────────────────────────────────
def save_extension_navigation(
    target_root: Path,
    extension: str,
    read_required_files: list[SkillFileRef],
    read_contextual_files: list[SkillFileRef],
) -> None:
    """Rewrite extension sections in spawn/navigation.yaml.
    Empty lists remove the corresponding extension section."""

def save_rules_navigation(target_root: Path) -> None:
    """Sync navigation with spawn/rules/:
    - add new rule files to read-required -> rules
    - remove navigation entries for missing rule files (with warning)
    """

# ── Init ─────────────────────────────────────────────────────────────────────
def init(target_root: Path) -> None:
    """Create spawn/, spawn/.core/config.yaml, spawn/.metadata/ide.yaml,
    spawn/.metadata/git-ignore.txt, spawn/rules/, spawn/navigation.yaml
    when missing. Idempotent."""
```

## Implementation notes

- **Frontmatter parsing** for skills: detect YAML frontmatter block (`---\n...\n---`) at top of skill `.md`; strip it and use `name`/`description` from there as defaults.
- **`generate_skills_metadata`**: collect descriptions from `SkillFileRef` objects; de-duplicate file paths preserving first description encountered.
- **Navigation read/write**: load current `navigation.yaml`, replace extension sections in place, write back. Navigation entries are identified by `ext` key.
- **`.gitignore` managed block**: push/remove only Spawn-owned lines. Track them via a comment sentinel:
  ```
  # spawn:start
  spawn/**
  !spawn/navigation.yaml
  # spawn:end
  ```
  Or simpler: compare against `git-ignore.txt` ownership list.
- **`init()`**: core config template must be loaded from CLI package resources (`importlib.resources`). Default core config content:
  ```yaml
  version: "0.1.0"
  agent-ignore:
    - spawn/**
    - "!spawn/navigation.yaml"
    - "!spawn/rules/**"
  ```

## Tests

`tests/core/test_low_level.py` using `tmp_path` (pytest fixture):

- `test_list_extensions_empty` — no extensions dir → `[]`
- `test_list_extensions` — create dirs under `.extend/` → correct list
- `test_add_remove_ide_to_list` — add, add again (idempotent), remove
- `test_get_required_read_global` — extension config with `globalRead: required` files → correct list
- `test_generate_skills_metadata` — mock extension with 2 skills, verify dedup of reads
- `test_list_mcp` — mcp.json with 1 server → NormalizedMcp with extension injected
- `test_save_get_rendered_skills` — write and read back
- `test_save_get_rendered_mcp` — write and read back
- `test_push_remove_global_gitignore` — idempotent push, selective remove
- `test_save_extension_navigation_empty_removes_section` — empty lists remove ext section
- `test_save_rules_navigation_new_rule` — new rule file added to read-required
- `test_save_rules_navigation_missing_rule_warns` — missing file removed with warning
- `test_init_idempotent` — run twice, no error
