# Step 3: Core High-Level Orchestration Modules

## Required reading
Before implementing, read:
- `spec/design/utility.md` — High-Level Modules, Download And Install, Extension Setup Modules, and Lifecycle Semantics sections
- `spec/design/extensions.md` — Setup Scripts, Static And Artifact Modes, and Authoring Workflow sections

## Goal
Implement all high-level module functions from `spec/design/utility.md` — refresh_*, remove_*, add_ide, remove_ide, extension lifecycle (install/update/uninstall), and download helpers.

## Approach
All functions live in `src/spawn_cli/core/high_level.py` and `src/spawn_cli/core/download.py`. They call low-level functions and IDE adapter registry. They do NOT call CLI parsing code. The **CLI** acquires **`spawn_lock`** for **all** commands (including read-only) after `spawn init` per `utility.md`.

## Affected files

```
src/spawn_cli/core/high_level.py
src/spawn_cli/core/download.py
src/spawn_cli/core/scripts.py
tests/core/test_high_level.py
tests/core/test_download.py
```

## `core/high_level.py` — function signatures

```python
from pathlib import Path
from spawn_cli.ide.registry import get as ide_get

# ── Ignore refresh ───────────────────────────────────────────────────────────
def refresh_gitignore(target_root: Path) -> None:
    """Rebuild Spawn-managed .gitignore entries from all installed extensions.
    new = union of all get_ext_git_ignore(ext)
    existing = get_git_ignore_list()
    push_to_global_gitignore(new - existing)
    remove_from_global_gitignore(existing - new)
    save_git_ignore_list(new)
    """

def refresh_agent_ignore(target_root: Path, ide: str) -> None:
    """old = get_agent_ignore_list; new = merged get_all_agent_ignore.
    remove_agent_ignore(old - new); add_agent_ignore(new - old) (or remove all old then add new).
    save_agent_ignore_list(ide, new).
    """

# ── Skills refresh ───────────────────────────────────────────────────────────
def refresh_skills(target_root: Path, ide: str, extension: str) -> None:
    """Validate global skill name uniqueness → remove old via metadata → add_skills →
    save rendered-skills.yaml only after successful add."""

def remove_skills(target_root: Path, ide: str, extension: str) -> None:
    """Remove paths from rendered-skills.yaml via adapter, then clear the section."""

# ── MCP refresh ──────────────────────────────────────────────────────────────
def refresh_mcp(target_root: Path, ide: str, extension: str) -> None:
    """Validate global MCP server name uniqueness → remove old via metadata → add_mcp →
    save rendered-mcp.yaml only after successful add."""

def remove_mcp(target_root: Path, ide: str, extension: str) -> None:
    """Remove names from rendered-mcp.yaml via adapter, then clear the section."""

# ── Entry point ──────────────────────────────────────────────────────────────
def refresh_entry_point(target_root: Path, ide: str) -> None:
    """Build standard Spawn entry point prompt → call ide.rewrite_entry_point(target_root, prompt)."""

SPAWN_ENTRY_POINT_PROMPT = """\
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the current task.
"""

# ── Per-IDE extension ops ────────────────────────────────────────────────────
def refresh_extension_for_ide(target_root: Path, ide: str, extension: str) -> None:
    """refresh_mcp + refresh_skills + refresh_agent_ignore for one IDE."""

def remove_extension_for_ide(target_root: Path, ide: str, extension: str) -> None:
    """remove_mcp + remove_skills + remove agent-ignore entries for one IDE."""

# ── Navigation ───────────────────────────────────────────────────────────────
def refresh_navigation(target_root: Path) -> None:
    """Rebuild navigation.yaml from all installed extensions + save_rules_navigation."""

def refresh_rules_navigation(target_root: Path) -> None:
    """Call save_rules_navigation only (spawn rules refresh CLI)."""

# ── Full extension lifecycle ─────────────────────────────────────────────────
def refresh_extension(target_root: Path, extension: str) -> None:
    """Run before-install scripts → refresh for every IDE → refresh gitignore,
    agent ignores, navigation → run after-install scripts."""

def remove_extension(target_root: Path, extension: str) -> None:
    """Run before-uninstall → remove rendered outputs for every IDE →
    remove static files/folders → remove installed extension folder →
    refresh ignores, navigation, and entry points → run after-uninstall."""

def update_extension(target_root: Path, extension: str) -> None:
    """Read source.yaml → download same source → validate → preserve artifacts →
    replace static extension source → run setup scripts → refresh everything.
    Error if same/older version and no force flag."""

def extension_healthcheck(target_root: Path, extension: str) -> bool:
    """Check config.yaml, skills, MCP, setup scripts, declared files/folders.
    Run healthcheck script. Returns True if healthy."""

def extension_init(path: Path, name: str) -> None:
    """Create development extension skeleton at {path}/extsrc/.
    Idempotent: warn and skip if extsrc/config.yaml already exists."""

def extension_check(path: Path, strict: bool = False) -> list[str]:
    """Validate extension source. Return list of warnings (strict: errors instead)."""

def extension_from_rules(source: str, output_path: Path, name: str, branch: Optional[str] = None) -> None:
    """Create extension source from existing target repository."""

# ── IDE lifecycle ────────────────────────────────────────────────────────────
def add_ide(target_root: Path, ide: str) -> None:
    """Add IDE to ide.yaml → detect → warn if skills/mcp insufficient →
    refresh_entry_point → refresh skills+MCP+agent-ignore for every installed extension."""

def remove_ide(target_root: Path, ide: str) -> None:
    """Remove rendered MCP + skills for every installed extension →
    remove agent-ignore → remove IDE from ide.yaml."""
```

## `core/download.py`

```python
def download_extension(target_root: Path, path: str, branch: Optional[str] = None) -> str:
    """Resolve git/zip/local source into target_root/spawn/.metadata/temp/{operation_id}/ when staging is needed.
    Reject zip entries that escape the staging directory (path traversal).
    Remove that directory in a finally block after the operation. Validate extsrc/config.yaml.
    Check cross-extension file conflicts, version rules, and source.yaml identity (see Key implementation details).
    Copy extsrc/ to spawn/.extend/{extension}.
    Write source.yaml.
    Returns extension name.
    Source types:
    - local path: shutil.copytree (staging optional)
    - git URL: subprocess git clone --depth 1 --branch {branch} into staging (requires `git` on PATH — else SpawnError with OS-specific install hints)
    - zip URL: httpx download into staging, zipfile.extract
    """

def install_extension(target_root: Path, path: str, branch: Optional[str] = None) -> None:
    """download_extension + refresh_extension."""

def list_build_extensions(path: str, branch: Optional[str] = None) -> list[dict]:
    """Resolve build source → read extensions.yaml → return [{path, branch}]."""

def install_build(target_root: Path, path: str, branch: Optional[str] = None) -> None:
    """list_build_extensions → install or refresh each extension."""
```

## `core/scripts.py`

```python
import subprocess

SCRIPT_ENV_VARS = ["SPAWN_EXT_NAME", "SPAWN_EXT_PATH", "SPAWN_EXT_VERSION",
                   "SPAWN_TARGET_VERSION", "SPAWN_TARGET_ROOT"]

def run_before_install_scripts(target_root: Path, extension: str) -> None:
    """Run before-install script if configured. Failure is blocking (SpawnError)."""

def run_after_install_scripts(target_root: Path, extension: str) -> None:
    """Run after-install script if configured. Failure is warning."""

def run_before_uninstall_scripts(target_root: Path, extension: str) -> None:
    """If `before-uninstall` is absent in config, return. If present, run it;
    failure raises SpawnError (blocking)."""

def run_after_uninstall_scripts(target_root: Path, extension: str) -> None:
    """Run after-uninstall script if configured. Failure is warning."""

def run_healthcheck_scripts(target_root: Path, extension: str) -> bool:
    """Run healthcheck script. Returns False on failure (no mutation)."""

def _run_script(target_root: Path, extension: str, script_name: str) -> subprocess.CompletedProcess:
    """Execute script with env vars set:
    SPAWN_TARGET_ROOT, SPAWN_EXT_NAME, SPAWN_EXT_PATH,
    SPAWN_EXT_VERSION, SPAWN_TARGET_VERSION (from source.yaml)
    cwd = target_root
    """
```

## Key implementation details

### Extension conflict check in `download_extension`
```python
def _check_path_conflicts(target_root: Path, candidate_config: ExtensionConfig, candidate_ext: str) -> None:
    for installed_ext in list_extensions(target_root):
        if installed_ext == candidate_ext:
            continue
        installed_config = _load_ext_config(target_root, installed_ext)
        for file_path in candidate_config.files:
            if file_path in installed_config.files:
                raise SpawnError(f"File conflict: {file_path} claimed by {installed_ext}")
        for folder in candidate_config.folders:
            if folder in installed_config.folders:
                raise SpawnError(f"Folder conflict: {folder} claimed by {installed_ext}")
```

### Version check in `download_extension` / `update_extension`
Use a **small in-tree version helper** (no third-party `packaging` dependency):
compare `config.yaml` `version` strings deterministically (for example split on
`.`, compare numeric segments; document the exact rule beside the helper).  
`SpawnError` when the candidate is **not strictly newer** than `source.yaml`’s
installed record where the spec requires an upgrade-only path.

### Source identity for `download_extension` / `install_extension`
If `spawn/.extend/{ext}/source.yaml` already exists for this extension name and the
resolved candidate source (type + path + branch identity) **does not match** the
stored record, **`SpawnError` before mutation**. User must **`remove_extension`**
then **`install_extension`** with the new source.  
`update_extension` ignores CLI paths: it re-reads only `source.yaml`.

### Static file materialization
```python
def _materialize_files(target_root: Path, extension: str, config: ExtensionConfig) -> None:
    """Copy static and artifact files from spawn/.extend/{ext}/files/ to target repo.
    static: overwrite (with warning if exists and not Spawn-owned)
    artifact: create only when missing
    """
```

### `extension_check` validations
1. `extsrc/config.yaml` exists
2. Referenced skill files exist under `extsrc/skills/`
3. Referenced setup scripts exist under `extsrc/setup/`
4. Files with `globalRead`/`localRead` != `no` have descriptions
5. Enum values valid
6. `mcp.json` parseable when present
7. Undeclared files in `extsrc/files/` → warning (strict: error)

### `extension_init` skeleton
Creates `extsrc/config.yaml`:
```yaml
name: {name}
schema: 1
version: "0.1.0"
files: {}
folders: {}
agent-ignore: []
git-ignore: []
skills: {}
setup: {}
```
Creates `extsrc/skills/`, `extsrc/files/`, `extsrc/setup/` dirs.

## Tests

`tests/core/test_high_level.py` using `tmp_path`:
- `test_refresh_gitignore` — install mock extension, check .gitignore updated
- `test_refresh_gitignore_removes_old` — second call removes no-longer-needed globs
- `test_refresh_agent_ignore` — mock adapter called with merged globs
- `test_refresh_skills` — validate uniqueness → remove old + render new, metadata saved only after add
- `test_refresh_skills_duplicate_name_errors` — second extension collides → SpawnError, no remove
- `test_refresh_mcp` — validate uniqueness → remove + add, metadata after add
- `test_refresh_mcp_duplicate_server_errors` — colliding MCP name → SpawnError before remove
- `test_remove_skills` — adapter remove_skills called, metadata cleared
- `test_refresh_entry_point` — adapter rewrite_entry_point called with prompt
- `test_refresh_rules_navigation` — delegates to `save_rules_navigation` only
- `test_add_ide` — ide.yaml updated, detect called, refresh called for each extension
- `test_remove_ide` — MCP/skills removed for all extensions, ide.yaml updated
- `test_refresh_extension` — before/after scripts called around refresh
- `test_remove_extension` — before/after scripts + rendered outputs removed + folder deleted
- `test_extension_init_creates_skeleton` — correct dirs and config.yaml created
- `test_extension_init_idempotent` — second call warns, leaves config unchanged
- `test_extension_check_valid` — no errors for valid extension
- `test_extension_check_missing_skill` — error on missing skill file
- `test_extension_check_missing_description` — error when read flag set but no description

`tests/core/test_download.py` using `tmp_path`:
- `test_download_local_path` — copy local extsrc into target
- `test_download_conflict_error` — two extensions claiming same file → SpawnError
- `test_download_version_check` — same version → SpawnError
- `test_install_build` — mock build manifest, all extensions installed
