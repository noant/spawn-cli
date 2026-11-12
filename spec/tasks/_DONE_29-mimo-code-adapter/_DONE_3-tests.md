# Step 3: Tests

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Add peer-parity tests for `MimoCodeAdapter` mirroring `tests/ide/test_opencode.py`, and extend `tests/ide/test_registry.py` alias/key assertions.

## Approach
Copy the `test_opencode.py` structure: module `adapter()` fixture, `_skill()` and `_stdio_server()` helpers, then per-concern tests for detect, skills roundtrip, MCP roundtrip + proxy, agent-ignore roundtrip/idempotency, entry-point managed block, config canonical-file warning/error, vacancy cleanup. Import paths change to `.mimocode` and `.mimocode/mimocode.json`.

## Affected files
- `tests/ide/test_mimo_code.py` — new test module
- `tests/ide/test_registry.py` — alias + key assertions
- `tests/ide/test_mcp_stdio_proxy_parity.py` — add `mimocode` parity param (MCP proxy golden check)

## Code changes (before / after)

### `tests/ide/test_mimo_code.py` — new module (insertion context: none)

**Before**
```python
# (no such file; tests/ide/test_opencode.py is the template)
```
No Mimo coverage; peer adapters each have a dedicated test module.

**After**
```python
"""Tests for the Mimo Code adapter."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.mimo_code import MimoCodeAdapter
from spawn_cli.models.mcp import McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> MimoCodeAdapter:
    return MimoCodeAdapter()


def _skill(name: str = "spectask-execute") -> SkillMetadata: ...
def _stdio_server(name: str = "srv", proxy: bool = False) -> McpServer: ...
```
Test coverage (mirroring `test_opencode.py` concern by concern):
- detect: `.mimocode/` dir marker; `used_in_repo` False on empty tmp_path; capabilities == native/project/project/agents-md.
- skills: add renders `.mimocode/skills/spectask-execute/SKILL.md` with frontmatter name == dirname; returns `{"skill", "path"}` posix rel path; overwrite emits `pytest.warns(SpawnWarning, match="Overwriting")`; remove unlinks SKILL.md and prunes the empty skill dir while keeping extra user files.
- MCP: add writes `.mimocode/mimocode.json` key `mcp` with `{"type": "local", "command": [...], "enabled": true}`; proxy variant renders `["spawn", "mcp_stdio", "extension", "ext", "name", "srv"]`; remote renders `{"type": "remote", "url": ...}` with `{env:K}` headers; remove pops entries and prunes the empty `mcp` key; idempotent remove on missing config.
- agent ignore: add writes `permission.read`/`permission.edit` glob -> `"deny"`; remove pops globs and prunes empty sections; idempotency; `clear_spawn_agent_ignore` uses `ll.get_agent_ignore_list` recording.
- canonical config (rule 05): when only `.mimocode/mimocode.jsonc` exists, mutation warns `SpawnWarning` and writes `.json`; invalid JSON raises `SpawnError`.
- entry point: `rewrite_entry_point` creates root `AGENTS.md` with `SPAWN_BLOCK_START`/`SPAWN_BLOCK_END` and re-renders in place.
- vacancy: `finalize_mimo_code_repo` deletes spawn-only vacant config, keeps user configs, prunes empty `.mimocode`.

### `tests/ide/test_registry.py` — key/alias assertions

**Before**
```python
# existing assertions cover CANONICAL_IDE_KEYS == detect_supported_ides keys;
# no mimo alias/get coverage
```
Registry tests assert full key parity but not the new alias.

**After**
```python
def test_get_mimo_alias(tmp_path):
    assert get("mimo").key == "mimo-code"

def test_mimo_code_in_supported_ides(tmp_path):
    assert "mimo-code" in detect_supported_ides(tmp_path)
```
Locks the new key and the `mimo` alias at registry level.

## Additional actions
Add `MimoCodeAdapter` to the `tests/ide/test_mcp_stdio_proxy_parity.py` parametrize list (`pytest.param(MimoCodeAdapter(), "mimocode_json", id="mimocode")`) plus a `read_entries == "mimocode_json"` branch reading `.mimocode/mimocode.json` and asserting via `_assert_stdio_wrapper_golden_opencode` (Mimo proxy emission is byte-identical to opencode). Run the test suite for the ide package: `python -m pytest tests/ide -q` (peer-parity check; no build step needed).
