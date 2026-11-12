# Step 3: Tests for Hermes adapter

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Add `tests/ide/test_hermes.py` mirroring peer adapter suites and extend registry/vacancy tests.

## Approach
Mirror `tests/ide/test_cline.py` (same file layout: `_skill()` SkillMetadata factory, `pytest.warns(UserWarning/SpawnWarning, match=...)`, ownership-dict `remove_skills(tmp_path, rendered)`). Do NOT modify `test_mcp_stdio_proxy_parity.py` (hermes mcp=unsupported — no parity param).

## Affected files
- `tests/ide/test_hermes.py` — new
- `tests/ide/test_registry.py` — extend `test_get_known_adapter`
- `tests/ide/test_vacancy.py` — add hermes finalize case

## Code changes (before / after)

### `tests/ide/test_hermes.py` — new (greenfield)

**Before**
```python
# no such file; mirror tests/ide/test_cline.py fixture pattern
```
No hermes test coverage.

**After**
```python
"""Tests for the Hermes IDE adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from spawn_cli.errors import SpawnWarning
from spawn_cli.ide.hermes import HermesAdapter
from spawn_cli.ide.registry import SPAWN_BLOCK_START
from spawn_cli.models.mcp import McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> HermesAdapter:
    return HermesAdapter()


def _skill(name: str = "spectask-execute") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Execute approved spectasks.",
        content="# body\n",
        hints=["Prefer spectask steps in order."],
    )


def _mcp() -> NormalizedMcp:
    return NormalizedMcp(
        servers=[
            {
                "name": "spectask-search",
                "extension": "spectask",
                "transport": McpTransport(type="stdio", command="uvx"),
            }
        ]
    )


def test_detect_markers(tmp_path: Path, adapter: HermesAdapter) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False
    (tmp_path / ".hermes").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_entry_file(tmp_path: Path, adapter: HermesAdapter) -> None:
    (tmp_path / ".hermes.md").write_text("x", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_capabilities(tmp_path: Path, adapter: HermesAdapter) -> None:
    caps = adapter.detect(tmp_path).capabilities
    assert caps.skills == "native"
    assert caps.mcp == "unsupported"
    assert caps.agent_ignore == "unsupported"
    assert caps.entry_point == "hermes-md"


def test_add_and_remove_skills(tmp_path: Path, adapter: HermesAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill("My Skill")])
    path = tmp_path / ".hermes" / "skills" / "my-skill" / "SKILL.md"
    assert path.is_file()
    assert rendered == [{"skill": "My Skill", "path": ".hermes/skills/my-skill/SKILL.md"}]
    text = path.read_text(encoding="utf-8")
    assert "name: my-skill" in text  # frontmatter name == directory name
    adapter.remove_skills(tmp_path, rendered)
    assert not path.exists()
    assert not path.parent.exists()


def test_add_skills_warns_on_overwrite(tmp_path: Path, adapter: HermesAdapter) -> None:
    adapter.add_skills(tmp_path, [_skill()])
    with pytest.warns(UserWarning, match="Overwriting"):
        adapter.add_skills(tmp_path, [_skill()])


def test_add_mcp_unsupported(tmp_path: Path, adapter: HermesAdapter) -> None:
    with pytest.warns(SpawnWarning, match="project-scope MCP"):
        assert adapter.add_mcp(tmp_path, _mcp()) == []
    assert not (tmp_path / ".hermes" / "mcp.json").exists()
    with pytest.warns(SpawnWarning):
        adapter.remove_mcp(tmp_path, ["spectask-search"])


def test_agent_ignore_unsupported_warns(tmp_path: Path, adapter: HermesAdapter) -> None:
    with pytest.warns(SpawnWarning):
        adapter.add_agent_ignore(tmp_path, ["secret/*"])
    with pytest.warns(SpawnWarning):
        adapter.remove_agent_ignore(tmp_path, ["secret/*"])


def test_entry_point_creates_and_replaces(tmp_path: Path, adapter: HermesAdapter) -> None:
    assert adapter.rewrite_entry_point(tmp_path, "first prompt") == ".hermes.md"
    ep = tmp_path / ".hermes.md"
    text = ep.read_text(encoding="utf-8")
    assert "first prompt" in text
    assert SPAWN_BLOCK_START in text
    assert adapter.rewrite_entry_point(tmp_path, "second prompt") == ".hermes.md"
    text = ep.read_text(encoding="utf-8")
    assert "second prompt" in text and "first prompt" not in text


def test_finalize_removes_vacant_hermes(tmp_path: Path, adapter: HermesAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    adapter.remove_skills(tmp_path, rendered)
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".hermes").exists()
```
Mirrors `tests/ide/test_cline.py` exactly: `_skill()` SkillMetadata factory, `pytest.warns(UserWarning/SpawnWarning, match=...)` (no manual catch_warnings), ownership dict with repo-relative posix path, `remove_skills(tmp_path, rendered)` list-of-dict contract.

### `tests/ide/test_registry.py` — extend known-adapter test

**Before**
```python
    assert isinstance(get("cline"), ClineAdapter)
    assert get("cline").key == "cline"
```
Known-adapter assertions per key (current last block in `test_get_known_adapter`, tests/ide/test_registry.py:47-48).

**After**
```python
    assert isinstance(get("cline"), ClineAdapter)
    assert get("cline").key == "cline"
    assert isinstance(get("hermes"), HermesAdapter)
    assert get("hermes").key == "hermes"
```
`get("hermes")` now resolves; add `HermesAdapter` to the existing `from spawn_cli.ide import (...)` block at the top of `tests/ide/test_registry.py` alongside `ClineAdapter` (the package re-exports it via `__init__.py`, per Step 1; do NOT import from `spawn_cli.ide.hermes` — the file imports all adapters from the package).

### `tests/ide/test_vacancy.py` — hermes finalize case

**Before**
```python
def test_finalize_opencode_repo_removes_vacant_config_and_dotdir(tmp_path: Path) -> None:
```
Vacancy pruners tested per adapter (codex/opencode present; tests/ide/test_vacancy.py:28); no hermes case.

**After**
```python
def test_finalize_hermes_repo_removes_vacant_dotdir(tmp_path: Path) -> None:
    (tmp_path / ".hermes" / "skills" / "s").mkdir(parents=True)
    finalize_hermes_repo(tmp_path)
    assert not (tmp_path / ".hermes").exists()


def test_finalize_hermes_repo_keeps_user_content(tmp_path: Path) -> None:
    (tmp_path / ".hermes" / "skills" / "s").mkdir(parents=True)
    (tmp_path / ".hermes" / "skills" / "s" / "SKILL.md").write_text("x", encoding="utf-8")
    (tmp_path / ".hermes" / "rules").mkdir()
    (tmp_path / ".hermes" / "rules" / "keep.md").write_text("rule", encoding="utf-8")
    finalize_hermes_repo(tmp_path)
    assert (tmp_path / ".hermes" / "rules" / "keep.md").is_file()
    assert (tmp_path / ".hermes").is_dir()
```
Confirms `.hermes/` dropped when vacant, kept with user files present (mirrors `test_finalize_opencode_repo_*` patterns); import `finalize_hermes_repo` from `spawn_cli.ide._vacancy` in the existing import line (tests/ide/test_vacancy.py:6).

## Additional actions
- Run: `pytest tests/ide/test_hermes.py tests/ide/test_registry.py tests/ide/test_vacancy.py -q`
- Then full: `pytest -q` — all green required.
