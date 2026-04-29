# Step 3: Core High-Level Orchestration Modules

## Required reading
Before implementing, read:
- `spec/design/utility.md` — High-Level Modules, Download And Install, Extension Setup Modules, and Lifecycle Semantics sections
- `spec/design/extensions.md` — Setup Scripts, Static And Artifact Modes, and Authoring Workflow sections

## Goal
Implement all high-level module functions from `spec/design/utility.md` — refresh_*, remove_*, add_ide, remove_ide, extension lifecycle (install/update/uninstall), and download helpers.

## Approach
All functions live in `src/spawn_cli/core/high_level.py` and `src/spawn_cli/core/download.py`. They call low-level functions and IDE adapter registry. They do NOT call CLI parsing code. The Spawn lock is acquired by the CLI layer before calling these functions.

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
    """Rebuild IDE agent ignore entries from core + all extension agent-ignore globs.
    Calls ide_get(ide).add_agent_ignore(target_root, new_globs).
    Saves new list via save_agent_ignore_list.
    """

# ── Skills refresh ───────────────────────────────────────────────────────────
def refresh_skills(target_root: Path, ide: str, extension: str) -> None:
    """Remove old rendered skills → generate fresh metadata → render via adapter → save paths."""

def remove_skills(target_root: Path, ide: str, extension: str) -> None:
    """Remove paths from rendered-skills.yaml via adapter, then clear the section."""

# ── MCP refresh ──────────────────────────────────────────────────────────────
def refresh_mcp(target_root: Path, ide: str, extension: str) -> None:
    """Remove old MCP → normalize mcp.json → render via adapter → save names."""

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
    """Resolve git/zip/local source into temp folder.
    Validate extsrc/config.yaml.
    Check cross-extension file conflicts.
    Check version/source rules.
    Copy extsrc/ to spawn/.extend/{extension}.
    Write source.yaml.
    Returns extension name.
    Source types:
    - local path: shutil.copytree
    - git URL: subprocess git clone --depth 1 --branch {branch}
    - zip URL: httpx download to temp, zipfile.extract
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
    """Run before-uninstall script if configured. Failure is blocking only if script marks required."""

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

### Version check in `download_extension`
```python
def _check_version(target_root: Path, ext_name: str, candidate_version: str) -> None:
    source_yaml_path = target_root / "spawn" / ".extend" / ext_name / "source.yaml"
    if source_yaml_path.exists():
        existing = SourceYaml.model_validate(load_yaml(source_yaml_path))
        if Version(candidate_version) <= Version(existing.installed.version):
            raise SpawnError(f"Candidate version {candidate_version} is not newer than installed {existing.installed.version}")
```

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
- `test_refresh_skills` — remove old + render new, metadata saved
- `test_remove_skills` — adapter remove_skills called, metadata cleared
- `test_refresh_entry_point` — adapter rewrite_entry_point called with prompt
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
