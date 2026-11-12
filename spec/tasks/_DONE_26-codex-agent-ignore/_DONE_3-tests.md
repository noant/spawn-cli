# Step 3: tests for codex agent ignore and vacancy cleanup

Status: Done
Suggested model: GLM-5.3-flash
Used model: GLM-5.3-flash

## Goal
Replace warn-stub tests with behavior tests for the permissions-profile implementation and add vacancy-cleanup coverage.

## Approach
- Mirror `tests/ide/test_cursor.py` L191-215 structure (add creates entries, remove preserves foreign content), adapted to TOML via `load_toml`.
- Cover: detect capability, add creates profile + extends + deny entries, add is idempotent, add warns on `sandbox_mode`, remove drops globs and prunes empty tables while preserving user content, clear via recorded state, finalize deletes config with empty spawn profile and preserves configs with real content.

## Affected files
- `tests/ide/test_codex.py` — `test_detect_with_codex_dir` (L24), replace `test_add_agent_ignore_warns` (L157-162) and `test_remove_agent_ignore_warns` (L165-169) with behavior tests.
- `tests/ide/test_vacancy.py` — new file (verified: no vacancy test file exists anywhere under tests/); codex finalize cases.

## Code changes (before / after)

### `tests/ide/test_codex.py` — capability assertion

**Before**
```python
    assert r.capabilities.agent_ignore == "unsupported"
```
Anchors the stub state.

**After**
```python
    assert r.capabilities.agent_ignore == "project"
```
Anchors the new project-config capability.

### `tests/ide/test_codex.py` — replace warn tests (L157-169)

**Before**
```python
def test_add_agent_ignore_warns(adapter: CodexAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_agent_ignore(tmp_path, ["**"])
        assert len(w) == 1
        assert "unsupported" in str(w[0].message).lower()


def test_remove_agent_ignore_warns(adapter: CodexAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.remove_agent_ignore(tmp_path, ["**"])
        assert len(w) == 1
```
Only assert warning emission; no behavior.

**After**
```python
def test_add_agent_ignore_writes_permissions_profile(adapter: CodexAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**", "secrets/**"])
    data = load_toml(tmp_path / ".codex" / "config.toml")
    fs = data["permissions"]["spawn"]["filesystem"][":workspace_roots"]
    assert fs["spawn/.core/**"] == "deny"
    assert fs["secrets/**"] == "deny"
    assert data["permissions"]["spawn"]["extends"] == ":workspace"


def test_add_agent_ignore_idempotent(adapter: CodexAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["a/**"])
    adapter.add_agent_ignore(tmp_path, ["a/**", "b/**"])
    data = load_toml(tmp_path / ".codex" / "config.toml")
    fs = data["permissions"]["spawn"]["filesystem"][":workspace_roots"]
    assert set(fs) == {"a/**", "b/**"}


def test_add_agent_ignore_warns_on_sandbox_mode(adapter: CodexAdapter, tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        'sandbox_mode = "danger-full-access"\n', encoding="utf-8"
    )
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_agent_ignore(tmp_path, ["a/**"])
        assert any("sandbox_mode" in str(x.message) for x in w)


def test_remove_agent_ignore_drops_globs_keeps_user_content(
    adapter: CodexAdapter, tmp_path: Path
) -> None:
    (tmp_path / ".codex").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        'other = "keep"\n\n[permissions.spawn.filesystem.":workspace_roots"]\n'
        '"a/**" = "deny"\n"b/**" = "deny"\n',
        encoding="utf-8",
    )
    adapter.remove_agent_ignore(tmp_path, ["a/**"])
    data = load_toml(tmp_path / ".codex" / "config.toml")
    assert data["other"] == "keep"
    assert set(data["permissions"]["spawn"]["filesystem"][":workspace_roots"]) == {"b/**"}


def test_remove_agent_ignore_prunes_empty_tables(adapter: CodexAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["a/**"])
    adapter.remove_agent_ignore(tmp_path, ["a/**"])
    data = load_toml(tmp_path / ".codex" / "config.toml")
    assert "permissions" not in data


def test_clear_spawn_agent_ignore_uses_recorded_state(
    adapter: CodexAdapter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter.add_agent_ignore(tmp_path, ["a/**", "b/**"])
    monkeypatch.setattr(
        ll, "get_agent_ignore_list", lambda root, key: ["a/**", "b/**"]
    )
    adapter.clear_spawn_agent_ignore(tmp_path)
    data = load_toml(tmp_path / ".codex" / "config.toml")
    assert "permissions" not in data
```
Behavior coverage for write/idempotency/warn/remove/prune/clear. Requires imports: `from spawn_cli.core import low_level as ll` (add to the test module imports; `pytest`, `warnings`, `load_toml` are already imported). The already-unused `IGNORE_BLOCK_END` / `IGNORE_BLOCK_START` imports (line 8) may be dropped in the same edit.

### `tests/ide/test_vacancy.py` — codex finalize cases (new file)

**Before**
(new file; insertion context: none)

**After** (file header with required imports):
```python
from __future__ import annotations

from pathlib import Path

from spawn_cli.ide._vacancy import finalize_codex_repo
```
followed by the tests:
```python
def test_finalize_codex_removes_config_with_empty_spawn_profile(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir(parents=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        '[permissions.spawn.filesystem.":workspace_roots"]\n', encoding="utf-8"
    )
    finalize_codex_repo(tmp_path)
    assert not (tmp_path / ".codex" / "config.toml").exists()


def test_finalize_codex_keeps_real_permissions(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir(parents=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        '[permissions.user.filesystem.":workspace_roots"]\n"x/**" = "deny"\n',
        encoding="utf-8",
    )
    finalize_codex_repo(tmp_path)
    assert (tmp_path / ".codex" / "config.toml").exists()
```
Empty spawn profile no longer blocks deletion; foreign profiles keep the file.

## Additional actions
- Run full subset: `pytest tests/ide/test_codex.py tests/ide/test_vacancy.py tests/ide/test_registry.py tests/core/test_high_level.py` — all green expected after Steps 1-2 (verified: `test_high_level.py` uses its own fake adapters and `test_registry.py` does not pin codex agent-ignore behavior, so the capability switch breaks neither).
- Check `grep -rn "agent_ignore" src/spawn_cli/cli.py` — expected: no codex-specific changes needed (report-only via capabilities.to_dict).
