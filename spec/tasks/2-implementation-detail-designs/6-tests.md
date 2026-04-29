# Step 6: Comprehensive Unit Tests

## Required reading
Before implementing, read:
- `spec/design/utility.md` — Core Rules, Lifecycle Semantics, and Rebuild Semantics sections (to understand what behaviors must be verified)
- `spec/design/data-structure.md` — Core Invariants section (invariants that tests should assert)

## Goal
Write full pytest unit test coverage for all modules implemented in steps 1–5. Each module has its own test file. Tests use `tmp_path`, mocking (`unittest.mock`), and no network calls.

## Approach
Tests are written after the implementation modules are complete. They use `pytest`, `tmp_path` fixture, and `unittest.mock.patch` / `MagicMock` for external calls (subprocess, httpx, filelock). Each test function is small and focused on one behavior.

## Affected files

```
tests/conftest.py             # shared fixtures
tests/models/test_config.py
tests/models/test_metadata.py
tests/models/test_navigation.py
tests/models/test_mcp.py
tests/models/test_skill.py
tests/io/test_yaml_io.py
tests/io/test_json_io.py
tests/io/test_toml_io.py
tests/io/test_text_io.py
tests/io/test_paths.py
tests/io/test_lock.py
tests/core/test_low_level.py
tests/core/test_high_level.py
tests/core/test_download.py
tests/core/test_scripts.py
tests/ide/test_registry.py
tests/ide/test_cursor.py
tests/ide/test_codex.py
tests/ide/test_claude_code.py
tests/ide/test_github_copilot.py
tests/ide/test_gemini_cli.py
tests/ide/test_windsurf.py
tests/test_cli.py
```

## `tests/conftest.py`

```python
import pytest
from pathlib import Path

@pytest.fixture
def target_root(tmp_path) -> Path:
    """A temp directory representing a target repository."""
    return tmp_path

@pytest.fixture
def spawn_root(target_root) -> Path:
    root = target_root / "spawn"
    root.mkdir()
    (root / ".metadata").mkdir()
    (root / ".extend").mkdir()
    (root / "rules").mkdir()
    (root / ".core").mkdir()
    return root

@pytest.fixture
def mock_extension(target_root, spawn_root) -> str:
    """Creates a minimal installed extension 'test-ext' with config, skills, mcp."""
    ext_dir = spawn_root / ".extend" / "test-ext"
    ext_dir.mkdir()
    (ext_dir / "skills").mkdir()
    (ext_dir / "files").mkdir()
    (ext_dir / "setup").mkdir()

    (ext_dir / "config.yaml").write_text("""
name: test-ext
version: "1.0.0"
schema: 1
files:
  methodology/guide.md:
    description: Core guide.
    mode: static
    globalRead: required
    localRead: required
agent-ignore:
  - spawn/.extend/**
git-ignore:
  - .spawn-cache/**
skills:
  test-skill.md:
    name: test-skill
    description: A test skill.
""", encoding="utf-8")

    (ext_dir / "skills" / "test-skill.md").write_text("""---
name: test-skill
description: A test skill.
---
Do the work.
""", encoding="utf-8")

    (ext_dir / "mcp.json").write_text("""
{
  "mcpServers": {
    "test-server": {
      "command": "uvx",
      "args": ["test-server-mcp"]
    }
  }
}
""", encoding="utf-8")
    return "test-ext"
```

## Test coverage requirements

### Models (tests/models/)
Each model module must test:
- Valid input parses correctly with expected field values
- Field aliases work (e.g. `required-read` → `required_read`)
- Default enum values applied when fields omitted
- Invalid enum values raise `ValidationError`
- Optional fields default to `None` or empty collections

### I/O helpers (tests/io/)
- `yaml_io`: round-trip save/load preserves data; missing file → `{}`; nested structures preserved
- `json_io`: round-trip; missing file → `{}`; indent applied
- `toml_io`: round-trip; missing file → `{}`
- `text_io`: write then read; missing file → `[]`; trailing newline handled
- `paths.py`: `safe_path` raises `SpawnError` on `..` escape; `ensure_dir` creates nested dirs
- `lock.py`: context manager acquires and releases; lock file created at expected path

### Low-level core (tests/core/test_low_level.py)
All functions listed in subtask `2-core-low-level.md`:
- Happy path for every function
- Edge cases: missing files return empty defaults; idempotent operations run twice without error
- `save_extension_navigation` with empty list removes extension section
- `save_rules_navigation` with new rule file adds to read-required; missing rule file removes and warns
- `push_to_global_gitignore` / `remove_from_global_gitignore`: preserve user content, only affect Spawn-owned lines
- `get_skill_raw_info`: frontmatter stripped from content; name/description resolved from frontmatter then from config override

### High-level core (tests/core/test_high_level.py)
All orchestration functions. Use mocked adapters:
```python
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.add_skills.return_value = [{"skill": "s.md", "path": ".cursor/skills/s/SKILL.md"}]
    adapter.add_mcp.return_value = ["test-server"]
    return adapter
```
- `refresh_skills`: adapter.remove_skills called with old paths, adapter.add_skills called, metadata saved
- `refresh_gitignore`: `.gitignore` updated, `git-ignore.txt` updated
- `add_ide`: ide.yaml updated, detect() called, refresh called per extension
- `remove_ide`: remove_skills + remove_mcp + remove_agent_ignore + ide.yaml updated
- `refresh_extension` / `remove_extension`: script runners called in correct order
- `extension_init`: correct skeleton files created; second call warns and leaves config unchanged
- `extension_check`: all validation paths covered

### Download (tests/core/test_download.py)
- `test_download_local_path`: copies local `extsrc/` to `.extend/{ext}`, writes `source.yaml`
- `test_download_git_url`: mocks `subprocess.run`, verifies clone args and temp path handling
- `test_download_zip_url`: mocks `httpx.get` and `zipfile.ZipFile`
- `test_download_version_error`: same version installed → `SpawnError`
- `test_download_conflict_error`: file conflict → `SpawnError`
- `test_install_build`: multiple extensions installed from mock manifest

### Scripts (tests/core/test_scripts.py)
- `test_run_before_install_success`: subprocess called, no exception
- `test_run_before_install_failure`: subprocess failure → `SpawnError`
- `test_run_after_install_failure`: subprocess failure → warning (no error)
- `test_no_script_configured`: runner returns without calling subprocess
- `test_env_vars_passed`: correct env vars in `Popen`/`run` call

### IDE adapters (tests/ide/)
For each of the 6 concrete adapters test all 7 operations (detect, add_skills, remove_skills, add_mcp, remove_mcp, add_agent_ignore, remove_agent_ignore, rewrite_entry_point).

Key cases to cover for each adapter:
- `detect` with and without IDE presence indicator (e.g. `.cursor/` dir)
- `add_skills` creates SKILL.md at correct path
- `add_skills` warns on overwrite
- `remove_skills` deletes file and cleans empty dir
- `add_mcp` creates/updates config file with correct format (JSON/TOML)
- `add_mcp` preserves existing non-Spawn entries
- `remove_mcp` removes only named servers
- `add_agent_ignore` creates managed block or merges into existing file
- `remove_agent_ignore` removes only Spawn-owned globs
- `rewrite_entry_point` creates entry file with spawn block
- `rewrite_entry_point` updates existing block without touching user content
- Windsurf `add_mcp` emits warning and returns `[]`
- Codex `add_agent_ignore` emits warning (unsupported)
- GitHub Copilot `add_agent_ignore` emits warning (unsupported)

### CLI (tests/test_cli.py)
All commands verified by patching the underlying utility functions with `unittest.mock.patch` and asserting they are called with correct arguments. Lock is also mocked.

```python
def test_spawn_init(tmp_path):
    with patch("spawn_cli.cli.ll.init") as mock_init, \
         patch("spawn_cli.cli.spawn_lock"):
        result = main(["--target", str(tmp_path), "init"])
    assert result == 0
    mock_init.assert_called_once_with(tmp_path)
```

## pytest configuration

`pyproject.toml` `[tool.pytest.ini_options]`:
```toml
testpaths = ["tests"]
addopts = "-v"
```

Ensure `tests/__init__.py` and `tests/models/__init__.py` etc. exist (or use `rootdir` detection).

## Coverage goal
- 100% of public functions called in at least one test
- Edge cases: empty inputs, missing files, idempotency, error paths
- No test should require network access or write outside `tmp_path`
