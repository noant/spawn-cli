# Step 4d: Claude Code IDE Adapter

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: IDE Matrix (Claude Code row), Skill Rendering (Markdown Skill Shape), MCP Rendering (Generic JSON MCP Shape), Entry Point Rendering (Claude Code row), Agent Ignore Rendering (Claude Code row), Ownership Records, Removal Semantics, Error And Warning Rules

## Prerequisite
Step 4a must be merged. All base abstractions and helpers are available from
`spawn_cli.ide.registry`.

## Goal
Implement `ClaudeCodeAdapter` — full concrete IDE adapter for Anthropic Claude Code
covering skills (`.claude/skills/`), MCP (`.mcp.json` at repo root), agent ignore
(`.claude/settings.json` permissions), and entry point (`CLAUDE.md`).

## Adapter surface map

| Surface | Target |
|---|---|
| Skills | `.claude/skills/{skill-name}/SKILL.md` |
| MCP | `.mcp.json` (repo root, `mcpServers` Generic JSON format) |
| Agent ignore | `.claude/settings.json` → `permissions.deny` list |
| Entry point | `CLAUDE.md` (managed HTML block) |

Detection signals: `.claude/` directory or `CLAUDE.md` exists at target root.

## Affected files

```
src/spawn_cli/ide/claude_code.py
tests/ide/test_claude_code.py
```

Also update `src/spawn_cli/ide/__init__.py` to uncomment the claude_code import.

## Implementation — `ide/claude_code.py`

### Skills

Written to `.claude/skills/{skill-name}/SKILL.md` using common Markdown skill shape.

### MCP

Repo-root `.mcp.json` using Generic JSON `mcpServers` format (same as Cursor but at root,
not under `.cursor/`). Merge strategy identical to Cursor: load → update `mcpServers` dict →
write back with stable `json.dumps(indent=2)`.

### Agent ignore — `permissions.deny` in `.claude/settings.json`

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Read(spawn/.metadata/**)"
    ]
  }
}
```

`add_agent_ignore`: load `.claude/settings.json` (empty `{}` if absent), ensure
`permissions.deny` list exists, append Spawn-owned globs (skip duplicates), write back.

`remove_agent_ignore`: load settings, remove only Spawn-owned globs from `permissions.deny`,
write back. Do not remove the key if it still contains user entries.

### Entry point

`CLAUDE.md` at target root. If `.claude/CLAUDE.md` also exists (alternate location),
Spawn writes to repo-root `CLAUDE.md` and warns that `.claude/CLAUDE.md` was not updated.
Use managed HTML block.

### Implementation skeleton

```python
import json
import warnings
from pathlib import Path
from spawn_cli.ide.registry import (
    IdeAdapter, IdeCapabilities, DetectResult, register,
    normalize_skill_name, render_skill_md, rewrite_managed_block,
)
from spawn_cli.models.skill import SkillMetadata
from spawn_cli.models.mcp import NormalizedMcp

class ClaudeCodeAdapter(IdeAdapter):
    key = "claude-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".claude").exists() or (target_root / "CLAUDE.md").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="project",
                entry_point="claude-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".claude" / "skills" / name
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
        """Merge into repo-root .mcp.json (mcpServers format)."""
        mcp_path = target_root / ".mcp.json"
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            data["mcpServers"][server.name] = _build_generic_mcp_entry(server)
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        mcp_path = target_root / ".mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        settings_path = target_root / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        deny = data.setdefault("permissions", {}).setdefault("deny", [])
        for glob in globs:
            if glob not in deny:
                deny.append(glob)
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        settings_path = target_root / ".claude" / "settings.json"
        if not settings_path.exists():
            return
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        deny = data.get("permissions", {}).get("deny", [])
        data["permissions"]["deny"] = [g for g in deny if g not in globs]
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "CLAUDE.md"
        if (target_root / ".claude" / "CLAUDE.md").exists():
            warnings.warn(
                "Claude Code: .claude/CLAUDE.md exists but Spawn writes to repo-root CLAUDE.md. "
                "Update .claude/CLAUDE.md manually if needed."
            )
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

register(ClaudeCodeAdapter())
```

Reuse `_build_generic_mcp_entry` from a shared location (or define locally if not yet extracted).

## Tests — `tests/ide/test_claude_code.py`

All tests use `tmp_path` fixture.

- `test_detect_with_claude_dir` — `.claude/` present → `used_in_repo=True`
- `test_detect_with_claude_md` — `CLAUDE.md` present → `used_in_repo=True`
- `test_detect_neither` → `used_in_repo=False`
- `test_add_skills_creates_under_claude` — path is `.claude/skills/{name}/SKILL.md`
- `test_add_skills_warns_on_overwrite`
- `test_remove_skills_deletes_file`
- `test_add_mcp_creates_root_mcp_json` — file at repo root (not under `.claude/`)
- `test_add_mcp_merges_existing`
- `test_add_mcp_secret_placeholder`
- `test_remove_mcp_removes_entry`
- `test_add_agent_ignore_updates_settings_deny` — `permissions.deny` list updated
- `test_add_agent_ignore_no_duplicates` — duplicate globs not added twice
- `test_remove_agent_ignore_removes_only_spawn_globs` — user entries preserved
- `test_remove_agent_ignore_missing_file_noop`
- `test_rewrite_entry_point_claude_md`
- `test_rewrite_entry_point_warns_alt_location` — `.claude/CLAUDE.md` exists → warning emitted
