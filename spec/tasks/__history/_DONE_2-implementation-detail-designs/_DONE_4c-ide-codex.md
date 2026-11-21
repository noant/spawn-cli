# Step 4c: Codex IDE Adapter

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: IDE Matrix (Codex row), Skill Rendering (Markdown Skill Shape), MCP Rendering (Codex TOML Shape), Entry Point Rendering (Codex row), Agent Ignore Rendering (Codex row), Ownership Records, Removal Semantics, Error And Warning Rules

## Prerequisite
Step 4a must be merged. All base abstractions and helpers are available from
`spawn_cli.ide.registry`.

## Goal
Implement `CodexAdapter` — full concrete IDE adapter for OpenAI Codex covering
skills (`.agents/skills/`), MCP (`.codex/config.toml` TOML format), no agent ignore
(warn-only), and entry point (`AGENTS.md`).

## Adapter surface map

| Surface | Target |
|---|---|
| Skills | `.agents/skills/{skill-name}/SKILL.md` |
| MCP | `.codex/config.toml` (`mcp_servers."name"` TOML table) |
| Agent ignore | Unsupported — emit warning |
| Entry point | `AGENTS.md` (managed HTML block) |

Detection signals: `.codex/` directory or `.agents/` directory exists at target root.

## Affected files

```
src/spawn_cli/ide/codex.py
tests/ide/test_codex.py
```

Also update `src/spawn_cli/ide/__init__.py` to uncomment the codex import.

## Implementation — `ide/codex.py`

### Skills

Skills are written to `.agents/skills/{skill-name}/SKILL.md` (OpenAI Codex discovers
project skills under `.agents/skills/`, not `.codex/`).

### MCP — TOML format

`config.toml` uses `mcp_servers` with **quoted** table keys for hyphenated names
(unquoted `spectask-search` is invalid TOML; it would be parsed as subtraction).

Stdio server:
```toml
[mcp_servers."spectask-search"]
command = "uvx"
args = ["spectask-search-mcp"]

[mcp_servers."spectask-search".env]
SPECTASK_TOKEN = "${SPECTASK_TOKEN}"
```

HTTP server:
```toml
[mcp_servers."spectask-search"]
url = "https://example.com/mcp"
```

Merging strategy:
- Load existing TOML (empty dict if absent).
- Add/overwrite `mcp_servers."name"` tables for Spawn-owned servers.
- Write back with `tomli_w` (or `tomllib`/`tomli` for reading, `tomli_w` for writing).

### Agent ignore

`add_agent_ignore` and `remove_agent_ignore` both emit a `warnings.warn` and return
without mutating any file. Codex has no upstream dedicated agent-ignore file.

### Entry point

`AGENTS.md` at target root, managed HTML block (same as Cursor).

### Stub implementation skeleton

```python
import warnings
import tomllib
import tomli_w
from pathlib import Path
from spawn_cli.ide.registry import (
    IdeAdapter, IdeCapabilities, DetectResult, register,
    normalize_skill_name, render_skill_md, rewrite_managed_block,
)
from spawn_cli.models.skill import SkillMetadata
from spawn_cli.models.mcp import NormalizedMcp

class CodexAdapter(IdeAdapter):
    key = "codex"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".codex").exists() or (target_root / ".agents").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="unsupported",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".agents" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            skill_path.write_text(render_skill_md(skill), encoding="utf-8")
            results.append({"skill": skill.name, "path": str(skill_path.relative_to(target_root))})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        config_path = target_root / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        data.setdefault("mcp_servers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            data["mcp_servers"][server.name] = _build_toml_server_entry(server)
            rendered_names.append(server.name)
        config_path.write_bytes(tomli_w.dumps(data).encode())
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        config_path = target_root / ".codex" / "config.toml"
        if not config_path.exists():
            return
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcp_servers", {}).pop(name, None)
        config_path.write_bytes(tomli_w.dumps(data).encode())

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        warnings.warn("codex: agent ignore is unsupported; steer via AGENTS.md policy instead")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        warnings.warn("codex: agent ignore is unsupported")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

register(CodexAdapter())
```

### TOML server entry builder

```python
def _build_toml_server_entry(server) -> dict:
    transport = server.transport
    entry: dict = {}
    if transport.type == "stdio":
        entry["command"] = transport.command
        entry["args"] = transport.args
    else:
        entry["url"] = transport.url
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else (v.value or f"${{{k}}}")
            for k, v in server.env.items()
        }
    return entry
```

## Tests — `tests/ide/test_codex.py`

All tests use `tmp_path` fixture.

- `test_detect_with_codex_dir` — `.codex/` present → `used_in_repo=True`
- `test_detect_with_agents_dir` — `.agents/` present → `used_in_repo=True`
- `test_detect_neither` → `used_in_repo=False`
- `test_add_skills_creates_under_agents` — path is `.agents/skills/{name}/SKILL.md`
- `test_add_skills_warns_on_overwrite`
- `test_remove_skills_deletes_file`
- `test_add_mcp_creates_toml` — `.codex/config.toml` created with quoted table key
- `test_add_mcp_merges_existing` — existing TOML preserved; Spawn table added
- `test_add_mcp_hyphenated_key_quoted` — server name `"spectask-search"` uses quoted key in TOML
- `test_add_mcp_secret_placeholder` — secret env rendered as `${VAR_NAME}`
- `test_remove_mcp_removes_table`
- `test_add_agent_ignore_warns` — `warnings.warn` called; no file written
- `test_remove_agent_ignore_warns`
- `test_rewrite_entry_point_agents_md`
