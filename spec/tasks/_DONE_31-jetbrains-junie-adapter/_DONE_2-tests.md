# Step 2: Tests for the Junie adapter

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Cover `JunieAdapter` with `tests/ide/test_junie.py` mirroring peer adapter tests, and add junie to the stdio proxy parity test.

## Approach
Copy the structure of `tests/ide/test_cursor.py` (detect, skills add/remove round-trip, overwrite warning, mcp.json merge/prune, agent-ignore roundtrip/idempotence/split/clear, entry-point create/replace) and `tests/ide/test_vacancy.py` finalize patterns. Run pytest and fix failures.

## Affected files
- `tests/ide/test_junie.py` — NEW
- `tests/ide/test_mcp_stdio_proxy_parity.py` — add junie param + `junie_json` entries reader

## Code changes (before / after)

### `tests/ide/test_junie.py` — NEW

**Before**
(insertion context: no `test_junie.py`; `junie` behavior untested)

**After**
```python
"""Tests for the JetBrains Junie IDE adapter (mirrors test_cursor.py / test_cline.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spawn_cli.errors import SpawnWarning
from spawn_cli.ide.junie import JunieAdapter
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> JunieAdapter:
    return JunieAdapter()


def _skill(name: str = "demo-skill") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Demo",
        content="Body",
        hints=["hint one"],
        required_read=[],
        auto_read=[],
    )


def _srv(name: str, *, proxy: bool = False, transport_type: str = "stdio") -> McpServer:
    return McpServer(
        name=name,
        extension="ext-a",
        spawn_stdio_proxy=proxy,
        transport=McpTransport(
            type=transport_type,
            command="tool-uv-name",
            args=["--flag"],
            cwd=".",
            url="https://example.test/mcp" if transport_type != "stdio" else None,
        ),
        env={"TOKEN": McpEnvVar(source="user", required=True, secret=True)},
    )
```
Fixtures and builders used by the tests below; same style as peer test files.

Test cases to implement (function names in `tests/ide/test_junie.py`):
- `test_detect_junie_dotdir` — `used_in_repo` True iff `(root/".junie").exists()`; capabilities `skills="native", mcp="project", agent_ignore="native", entry_point="agents-md"`.
- `test_add_and_remove_skills_roundtrip` — renders `.junie/skills/demo-skill/SKILL.md` with frontmatter name `demo-skill`; removal unlinks file and prunes empty skill dir; keeps extra user files.
- `test_add_skills_overwrite_warns` — second `add_skills` on same name emits `SpawnWarning` "Overwriting existing rendered skill" (rule 03; `pytest.warns(SpawnWarning)`).
- `test_add_skills_frontmatter_name_matches_dir` — skill named `"My Skill"` renders into `.junie/skills/my-skill/SKILL.md` with frontmatter `name: my-skill` (rule 04: frontmatter name == dir name, enforced by `model_copy(update={"name": name})`).
- `test_add_mcp_creates_and_merges` — creates `.junie/mcp/mcp.json` with `mcpServers` entries; merging preserves an existing user server entry.
- `test_add_mcp_proxy_entry_uses_spawn_wrapper` — `spawn_stdio_proxy=True` yields `{"command": "spawn", "args": mcp_stdio_argv("ext-a", name)}` and no inner command.
- `test_add_mcp_remote_entry_shape` — `streamable-http` yields `{"type": "streamable-http", "url": ...}` (+ headers when set); secret env renders `${KEY}`.
- `test_remove_mcp_prunes_entries` — names removed; file remains with other servers; removing last server leaves empty `mcpServers` map (file kept; finalize handles unlink).
- `test_agent_ignore_roundtrip_and_clear` — `add_agent_ignore` writes `# spawn:start/end` block in `.aiignore`; idempotent re-add; `remove_agent_ignore` drops globs; `clear_spawn_agent_ignore` empties block; split-region methods work like cursor.
- `test_rewrite_entry_point_agents_md` — creates root `AGENTS.md` with `<!-- spawn:start -->`/`<!-- spawn:end -->` block; second call replaces block; returns `"AGENTS.md"`.
- `test_finalize_repo_after_ide_removed` (parametrized) — (a) only spawn artifacts: skills removed + mcp.json empty -> `.junie` and `mcp/mcp.json` unlinked, `.aiignore` unlinked when only spawn block; (b) user content present (`".junie/rules/r.md"`, `".junie/memory/x.md"`): `.junie` kept, spawn-owned parts still pruned, `.aiignore` with user lines kept minus spawn block.

Behavior line: all tests pass under `pytest tests/ide/test_junie.py`.

### `tests/ide/test_mcp_stdio_proxy_parity.py` — add junie param

**Before**
```python
from spawn_cli.ide.opencode import OpenCodeAdapter
```
Parity test adapters import list.

**After**
```python
from spawn_cli.ide.opencode import OpenCodeAdapter
from spawn_cli.ide.junie import JunieAdapter
```
Enables junie in the parity suite.

**Before**
```python
        pytest.param(OpenCodeAdapter(), "opencode_json", id="opencode"),
    ],
)
```
Parametrize list of adapters under parity test.

**After**
```python
        pytest.param(OpenCodeAdapter(), "opencode_json", id="opencode"),
        pytest.param(JunieAdapter(), "junie_json", id="junie"),
    ],
)
```
Adds the junie case; junie uses the cursor-style `mcpServers` JSON map.

Add a `junie_json` branch to the entries-reader dispatch (same file), mirroring the `cursor_json` branch exactly (read `.junie/mcp/mcp.json`, per-name lookup `dict(data["mcpServers"][name])` per the dispatch's existing if/elif convention) and use the standard `_assert_stdio_wrapper_golden` (not the opencode variant). Inspect the existing dispatch (functions consuming the `read_entries` label) and follow its exact convention.

Note: `tests/ide/test_registry.py::test_detect_supported_ides` asserts `list(out.keys()) == list(CANONICAL_IDE_KEYS)` and calls `get(key).detect()` for every key — it starts covering `junie` automatically once registered; no edit needed there.

## Additional actions
- Run: `pytest tests/ide/ -q` — all green.
- Run: `pytest tests/ide/test_registry.py -q` — confirms detect order matches the appended `CANONICAL_IDE_KEYS`.
