# Step 2: Vacancy cleanup helper

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Add `finalize_opencode_repo` to `src/spawn_cli/ide/_vacancy.py`, wire it into `OpenCodeAdapter.finalize_repo_after_ide_removed`, and cover it in `tests/ide/test_vacancy.py`.

## Approach
Follow `spawn/rules/01-vacancy-cleanup-subtrees.md`: the helper must know every adapter-written config subtree — root `opencode.json` keys `mcp` and `permission`, plus `.opencode/skills`. Delete the file only when vacant (no user content in known keys); never delete user content. Precedents: `finalize_claude_repo` (root-config key awareness) and `finalize_cline_repo` (dotdir skills prune).

## Affected files
- `src/spawn_cli/ide/_vacancy.py` — NEW `finalize_opencode_repo`; `__all__` entry
- `src/spawn_cli/ide/opencode.py` — `finalize_repo_after_ide_removed` override
- `tests/ide/test_vacancy.py` — finalize tests

## Code changes (before / after)

### `src/spawn_cli/ide/_vacancy.py` — NEW function `finalize_opencode_repo`
**Before**
(nothing to quote; insertion context: sibling `finalize_cline_repo(target_root)` at `_vacancy.py:229-240`)
New helper; no cleanup exists for OpenCode-written subtrees.
**After**
```python
_OPENCODE_CONFIG = "opencode.json"


def _opencode_config_vacant(path: Path) -> bool:
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


def finalize_opencode_repo(target_root: Path) -> None:
    """OpenCode adapter: root `opencode.json` (keys mcp, permission) and `.opencode/skills`; drop when vacant."""
    config = target_root / _OPENCODE_CONFIG
    if config.is_file():
        try:
            vacant = _opencode_config_vacant(config)
        except json.JSONDecodeError:
            vacant = False  # keep unparseable user config untouched
        if vacant:
            config.unlink()
    skills_dir = target_root / ".opencode" / "skills"
    if skills_dir.is_dir() and not dir_has_any_file(skills_dir):
        prune_empty_directories_under(target_root / ".opencode")
    if (target_root / ".opencode").is_dir() and not dir_has_any_file(target_root / ".opencode"):
        (target_root / ".opencode").rmdir()
```
Removes spawn-owned empty subtrees per rule 01 (file empty, or only known keys `mcp`/`permission` and all empty); deletes `opencode.json` only then, prunes `.opencode` when it holds no files.
(Exact helper names/signatures of `dir_has_any_file`, `prune_empty_directories_under`, `json_value_nonempty` are as in `_vacancy.py`; reuse them, do not duplicate logic.)
**Before**
```python
    "finalize_cline_repo",
```
`__all__` entry.
**After**
```python
    "finalize_cline_repo",
    "finalize_opencode_repo",
```
Export the new helper.

### `src/spawn_cli/ide/opencode.py` — wire finalize
**Before**
```python
    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()
```
Adapter class end; no finalize override (base class no-op).
**After**
```python
    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_opencode_repo(target_root)
```
Delegates IDE-removal cleanup to the vacancy helper.
Plus the imports at the top of `opencode.py`:
**Before**
```python
from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
```
Import block start.
**After**
```python
from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import _vacancy as _vac
```
Vacancy module import (cline precedent).

### `tests/ide/test_vacancy.py` — finalize tests
**Before**
(nothing to quote; insertion context: existing per-adapter finalize tests in the same module)
No coverage for `finalize_opencode_repo`.
**After**
```python
def test_finalize_opencode_repo_removes_vacant_config_and_dotdir(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / ".opencode" / "skills" / "s").mkdir(parents=True)
    finalize_opencode_repo(tmp_path)
    assert not (tmp_path / "opencode.json").exists()
    assert not (tmp_path / ".opencode").exists()


def test_finalize_opencode_repo_keeps_user_only_keys(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"model": "x", "theme": "dark"}), encoding="utf-8"
    )
    finalize_opencode_repo(tmp_path)
    assert (tmp_path / "opencode.json").exists()


def test_finalize_opencode_repo_keeps_user_content(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"model": "x", "mcp": {}, "permission": {"read": {"user/**": "ask"}}}),
        encoding="utf-8",
    )
    (tmp_path / ".opencode" / "skills" / "s" / "SKILL.md").parent.mkdir(parents=True)
    (tmp_path / ".opencode" / "skills" / "s" / "SKILL.md").write_text("x", encoding="utf-8")
    finalize_opencode_repo(tmp_path)
    assert (tmp_path / "opencode.json").exists()
    assert (tmp_path / ".opencode" / "skills" / "s" / "SKILL.md").exists()
```
Vacant config + empty dotdir are removed; user keys and skill files survive. Add missing imports (`json`, `finalize_opencode_repo`) following the module's existing import style.

## Additional actions
- Run `python -m pytest tests/ide/test_vacancy.py tests/ide/test_opencode.py -q`, then the full suite `python -m pytest -q`.
