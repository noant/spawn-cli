# Step 4f: Gemini CLI IDE Adapter

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: IDE Matrix (Gemini CLI row), Skill Rendering (Markdown Skill Shape), MCP Rendering (Qwen / Gemini Settings Shape), Entry Point Rendering (Gemini CLI row), Agent Ignore Rendering (Gemini CLI row), Ownership Records, Removal Semantics, Error And Warning Rules

## Prerequisite
Step 4a must be merged. All base abstractions and helpers are available from
`spawn_cli.ide.registry`.

## Goal
Implement `GeminiCliAdapter` — full concrete IDE adapter for Google Gemini CLI
covering skills (`.gemini/skills/`), MCP (`.gemini/settings.json` `mcpServers`),
agent ignore (`.geminiignore` managed block), and entry point (`GEMINI.md`).

## Adapter surface map

| Surface | Target |
|---|---|
| Skills | `.gemini/skills/{skill-name}/SKILL.md` |
| MCP | `.gemini/settings.json` → `mcpServers` (Generic JSON / Gemini format) |
| Agent ignore | `.geminiignore` (managed `# spawn:start` block) |
| Entry point | `GEMINI.md` (managed HTML block) |

Detection signal: `.gemini/` directory or `GEMINI.md` exists at target root.

## Affected files

```
src/spawn_cli/ide/gemini_cli.py
tests/ide/test_gemini_cli.py
```

Also update `src/spawn_cli/ide/__init__.py` to uncomment the gemini_cli import.

## Implementation — `ide/gemini_cli.py`

### Skills

Written to `.gemini/skills/{skill-name}/SKILL.md` using common Markdown skill shape.

### MCP — `.gemini/settings.json`

The project settings file is `.gemini/settings.json` at repo root.
It uses `mcpServers` key (same family as Generic JSON shape).

For HTTP servers, the Gemini format uses `httpUrl` for streamable HTTP and `url` for SSE:

```json
{
  "mcpServers": {
    "spectask-search": {
      "httpUrl": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${SPECTASK_TOKEN}"
      }
    }
  }
}
```

For stdio servers, the shape is identical to Generic JSON:

```json
{
  "mcpServers": {
    "spectask-search": {
      "command": "uvx",
      "args": ["spectask-search-mcp"],
      "env": {"SPECTASK_TOKEN": "${SPECTASK_TOKEN}"}
    }
  }
}
```

Merging strategy: load existing `.gemini/settings.json` (empty `{}` if absent),
update `mcpServers` dict, write back with `json.dumps(indent=2)`.

### Agent ignore — `.geminiignore`

Uses managed `# spawn:start` / `# spawn:end` text block (same style as `.cursorignore`).
Uses `rewrite_ignore_block` / `remove_ignore_block` helpers from `registry.py`.

### Entry point

`GEMINI.md` at target root. Uses managed HTML block.
Gemini CLI may also read context filenames from `.gemini/settings.json`
(`context.fileName`). Spawn writes only to `GEMINI.md` by default and does not
mutate `context.fileName` unless explicitly required.

### Implementation skeleton

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

class GeminiCliAdapter(IdeAdapter):
    key = "gemini-cli"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".gemini").exists() or (target_root / "GEMINI.md").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="native",
                entry_point="gemini-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".gemini" / "skills" / name
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
        settings_path = target_root / ".gemini" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            data["mcpServers"][server.name] = _build_gemini_mcp_entry(server)
            rendered_names.append(server.name)
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        settings_path = target_root / ".gemini" / "settings.json"
        if not settings_path.exists():
            return
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".geminiignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".geminiignore", globs)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "GEMINI.md"
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

register(GeminiCliAdapter())
```

### Gemini MCP entry builder

```python
def _build_gemini_mcp_entry(server) -> dict:
    transport = server.transport
    entry: dict = {}
    if transport.type == "stdio":
        entry["command"] = transport.command
        entry["args"] = transport.args
    elif transport.type == "streamable-http":
        entry["httpUrl"] = transport.url
        if transport.headers:
            entry["headers"] = {k: f"Bearer ${{{v}}}" if "auth" in k.lower() else f"${{{v}}}"
                                 for k, v in transport.headers.items()}
    elif transport.type == "sse":
        entry["url"] = transport.url
        if transport.headers:
            entry["headers"] = transport.headers
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else (v.value or f"${{{k}}}")
            for k, v in server.env.items()
        }
    return entry
```

## Tests — `tests/ide/test_gemini_cli.py`

All tests use `tmp_path` fixture.

- `test_detect_with_gemini_dir` — `.gemini/` present → `used_in_repo=True`
- `test_detect_with_gemini_md` — `GEMINI.md` present → `used_in_repo=True`
- `test_detect_neither` → `used_in_repo=False`
- `test_add_skills_creates_under_gemini` — path is `.gemini/skills/{name}/SKILL.md`
- `test_add_skills_warns_on_overwrite`
- `test_remove_skills_deletes_file`
- `test_add_mcp_creates_settings_json` — `.gemini/settings.json` created with `mcpServers`
- `test_add_mcp_merges_existing_settings` — existing settings keys preserved
- `test_add_mcp_stdio_shape` — entry has `command` and `args`
- `test_add_mcp_http_uses_http_url` — streamable-HTTP transport renders `httpUrl`
- `test_add_mcp_sse_uses_url` — SSE transport renders `url`
- `test_add_mcp_secret_placeholder`
- `test_remove_mcp_removes_entry`
- `test_add_agent_ignore_creates_geminiignore` — managed block written
- `test_remove_agent_ignore_removes_block`
- `test_rewrite_entry_point_gemini_md`
