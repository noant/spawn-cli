# Step 4b: Cursor IDE Adapter

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: IDE Matrix (Cursor row), Skill Rendering (Cursor Native Skill Shape, Cursor MDC Fallback Shape), MCP Rendering (Generic JSON MCP Shape), Entry Point Rendering, Agent Ignore Rendering (Cursor row), Ownership Records, Removal Semantics, Error And Warning Rules

## Prerequisite
Step 4a must be merged. `IdeAdapter`, `register`, `render_skill_md`, `rewrite_managed_block`,
`normalize_skill_name`, and `rewrite_ignore_block` / `remove_ignore_block` are imported from
`spawn_cli.ide.registry`.

## Goal
Implement `CursorAdapter` — a full concrete IDE adapter for the Cursor editor covering
skills, MCP (`.cursor/mcp.json`), agent ignore (`.cursorignore`), and entry point (`AGENTS.md`).

## Adapter surface map

| Surface | Target |
|---|---|
| Skills | `.cursor/skills/{skill-name}/SKILL.md` |
| MCP | `.cursor/mcp.json` (Generic JSON `mcpServers`) |
| Agent ignore | `.cursorignore` (managed block) |
| Entry point | `AGENTS.md` (managed HTML block) |

Detection signal: `.cursor/` directory exists at target root.

## Affected files

```
src/spawn_cli/ide/cursor.py
tests/ide/test_cursor.py
```

Also update `src/spawn_cli/ide/__init__.py` to uncomment the cursor import.

## Implementation — `ide/cursor.py`

```python
import json
import warnings
from pathlib import Path
from spawn_cli.ide.registry import (
    IdeAdapter, IdeCapabilities, DetectResult, register,
    normalize_skill_name, render_skill_md, rewrite_managed_block,
    rewrite_ignore_block, remove_ignore_block,
)
from spawn_cli.models.skill import SkillMetadata
from spawn_cli.models.mcp import NormalizedMcp

class CursorAdapter(IdeAdapter):
    key = "cursor"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".cursor").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="native",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".cursor" / "skills" / name
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
        """Merge Spawn-owned servers into .cursor/mcp.json (mcpServers format)."""
        mcp_path = target_root / ".cursor" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            entry = _build_mcp_server_entry(server)
            data["mcpServers"][server.name] = entry
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        """Remove named entries from .cursor/mcp.json."""
        mcp_path = target_root / ".cursor" / "mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".cursorignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".cursorignore", globs)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

register(CursorAdapter())
```

### MCP entry builder (Generic JSON shape)

```python
def _build_mcp_server_entry(server) -> dict:
    """Convert NormalizedMcpServer to .cursor/mcp.json entry (mcpServers format)."""
    transport = server.transport
    if transport.type == "stdio":
        entry: dict = {"command": transport.command, "args": transport.args}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": transport.type, "url": transport.url}
        if transport.headers:
            entry["headers"] = {k: f"${{{v}}}" for k, v in transport.headers.items()}
    else:
        entry = {"command": transport.command, "args": transport.args}
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else v.value or f"${{{k}}}"
            for k, v in server.env.items()
        }
    return entry
```

Secrets are rendered as `"${VAR_NAME}"` placeholder strings. Spawn must not write
actual secret values.

## Tests — `tests/ide/test_cursor.py`

All tests use `tmp_path` fixture.

- `test_detect_with_cursor_dir` — `.cursor/` present → `used_in_repo=True`, all capability fields correct
- `test_detect_without_cursor_dir` — `.cursor/` absent → `used_in_repo=False`
- `test_add_skills_creates_file` — `SKILL.md` created at `.cursor/skills/{name}/SKILL.md`; content has frontmatter + nav line
- `test_add_skills_warns_on_overwrite` — existing `SKILL.md` triggers `warnings.warn`
- `test_add_skills_returns_tracking_list` — returned list has `{skill, path}` for each skill
- `test_remove_skills_deletes_file` — file unlinked; empty skill dir removed
- `test_remove_skills_keeps_non_empty_dir` — non-empty skill dir not removed
- `test_add_mcp_creates_file` — `.cursor/mcp.json` created with correct `mcpServers` entry
- `test_add_mcp_merges_existing` — existing `.cursor/mcp.json` content preserved; Spawn entry added
- `test_add_mcp_secret_placeholder` — secret env var rendered as `${VAR_NAME}`, not literal value
- `test_remove_mcp_removes_entry` — named server removed from `mcpServers`; other entries untouched
- `test_remove_mcp_missing_file_noop` — no file → no error
- `test_add_agent_ignore` — `.cursorignore` updated with managed `# spawn:start` block
- `test_remove_agent_ignore` — managed block updated; Spawn-owned globs removed; user globs preserved
- `test_rewrite_entry_point_creates` — `AGENTS.md` absent → file created with spawn block
- `test_rewrite_entry_point_replaces` — existing `AGENTS.md` spawn block replaced, surrounding content kept
- `test_rewrite_entry_point_returns_path` — returns `"AGENTS.md"` relative path string
