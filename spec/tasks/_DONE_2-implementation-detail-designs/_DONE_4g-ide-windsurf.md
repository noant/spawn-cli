# Step 4g: Windsurf IDE Adapter

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: IDE Matrix (Windsurf row), Skill Rendering (Markdown Skill Shape), MCP Rendering (Windsurf row — unsupported), Entry Point Rendering (Windsurf row), Agent Ignore Rendering (Windsurf row), Ownership Records, Removal Semantics, Error And Warning Rules

## Prerequisite
Step 4a must be merged. All base abstractions and helpers are available from
`spawn_cli.ide.registry`.

## Goal
Implement `WindsurfAdapter` — full concrete IDE adapter for Windsurf covering
skills (`.windsurf/skills/`), no MCP (warn-only), agent ignore (`.codeiumignore`
managed block), and entry point (`AGENTS.md`).

## Adapter surface map

| Surface | Target |
|---|---|
| Skills | `.windsurf/skills/{skill-name}/SKILL.md` |
| MCP | Unsupported — emit warning |
| Agent ignore | `.codeiumignore` (managed `# spawn:start` block) |
| Entry point | `AGENTS.md` (managed HTML block) |

Detection signal: `.windsurf/` directory or `.codeiumignore` exists at target root.

## Affected files

```
src/spawn_cli/ide/windsurf.py
tests/ide/test_windsurf.py
```

Also update `src/spawn_cli/ide/__init__.py` to uncomment the windsurf import.

## Implementation — `ide/windsurf.py`

### Skills

Written to `.windsurf/skills/{skill-name}/SKILL.md` using common Markdown skill shape.

### MCP — unsupported

Windsurf has no documented committed project MCP schema (MCP is historically user-global
in Cascade). `add_mcp` emits a warning and returns `[]`. `remove_mcp` emits a warning
and returns without mutation.

### Agent ignore — `.codeiumignore`

Uses managed `# spawn:start` / `# spawn:end` text block.
Uses `rewrite_ignore_block` / `remove_ignore_block` helpers.

### Entry point

`AGENTS.md` at target root. Uses managed HTML block.

### Implementation

```python
import warnings
from pathlib import Path
from spawn_cli.ide.registry import (
    IdeAdapter, IdeCapabilities, DetectResult, register,
    normalize_skill_name, render_skill_md, rewrite_managed_block,
    rewrite_ignore_block, remove_ignore_block,
)
from spawn_cli.models.skill import SkillMetadata
from spawn_cli.models.mcp import NormalizedMcp

class WindsurfAdapter(IdeAdapter):
    key = "windsurf"

    def detect(self, target_root: Path) -> DetectResult:
        used = (
            (target_root / ".windsurf").exists()
            or (target_root / ".codeiumignore").exists()
        )
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="unsupported",
                agent_ignore="native",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".windsurf" / "skills" / name
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
        warnings.warn(
            "windsurf: Windsurf does not support project MCP config; "
            "MCP is configured globally in Cascade"
        )
        return []

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        warnings.warn("windsurf: MCP is unsupported; nothing to remove")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".codeiumignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".codeiumignore", globs)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

register(WindsurfAdapter())
```

## Tests — `tests/ide/test_windsurf.py`

All tests use `tmp_path` fixture.

- `test_detect_with_windsurf_dir` — `.windsurf/` present → `used_in_repo=True`
- `test_detect_with_codeiumignore` — `.codeiumignore` present → `used_in_repo=True`
- `test_detect_neither` → `used_in_repo=False`
- `test_capabilities_mcp_unsupported` — `capabilities.mcp == "unsupported"`
- `test_add_skills_creates_under_windsurf` — path is `.windsurf/skills/{name}/SKILL.md`
- `test_add_skills_warns_on_overwrite`
- `test_remove_skills_deletes_file`
- `test_add_mcp_warns_and_returns_empty` — warning emitted; returns `[]`; no file written
- `test_remove_mcp_warns` — warning emitted; no file written
- `test_add_agent_ignore_creates_codeiumignore` — managed block written to `.codeiumignore`
- `test_remove_agent_ignore_removes_block`
- `test_rewrite_entry_point_agents_md`
