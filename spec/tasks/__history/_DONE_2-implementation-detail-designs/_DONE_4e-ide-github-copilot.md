# Step 4e: GitHub Copilot IDE Adapter

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: IDE Matrix (GitHub Copilot row), Skill Rendering (GitHub Copilot Instructions Shape, Markdown Skill Shape), MCP Rendering (VS Code / Copilot MCP Shape), Entry Point Rendering (GitHub Copilot row), Agent Ignore Rendering (GitHub Copilot row), Ownership Records, Removal Semantics, Error And Warning Rules

## Prerequisite
Step 4a must be merged. All base abstractions and helpers are available from
`spawn_cli.ide.registry`.

## Goal
Implement `GitHubCopilotAdapter` — full concrete IDE adapter for GitHub Copilot
covering skills (`.github/skills/`), MCP (`.vscode/mcp.json` VS Code format with
`servers` + `inputs`), no agent ignore (warn-only), and entry point
(`.github/copilot-instructions.md` + root `AGENTS.md`).

## Adapter surface map

| Surface | Target |
|---|---|
| Skills | `.github/skills/{skill-name}/SKILL.md` |
| MCP | `.vscode/mcp.json` (`servers` + `inputs` VS Code format) |
| Agent ignore | Unsupported — emit warning |
| Entry point | `.github/copilot-instructions.md` (managed HTML block) **and** root `AGENTS.md` (managed HTML block) |

Detection signals: `.github/` directory or `.vscode/` directory exists.

## Affected files

```
src/spawn_cli/ide/github_copilot.py
tests/ide/test_github_copilot.py
```

Also update `src/spawn_cli/ide/__init__.py` to uncomment the github_copilot import.

## Implementation — `ide/github_copilot.py`

### Skills

Written to `.github/skills/{skill-name}/SKILL.md` using common Markdown skill shape.

### MCP — VS Code format

`.vscode/mcp.json` uses **`servers`** (not `mcpServers`) at the top level, plus optional
**`inputs`** array for secrets.

For `secret: true` env vars, the adapter must:
1. Generate an `inputs` entry: `{"id": "...", "type": "promptString", "description": "...", "password": true}`.
2. Reference it in the server entry as `"${input:id}"`.

```json
{
  "servers": {
    "spectask-search": {
      "type": "stdio",
      "command": "uvx",
      "args": ["spectask-search-mcp"],
      "env": {
        "SPECTASK_TOKEN": "${input:spectask-token}"
      }
    }
  },
  "inputs": [
    {
      "id": "spectask-token",
      "type": "promptString",
      "description": "SPECTASK_TOKEN",
      "password": true
    }
  ]
}
```

Merging strategy for `add_mcp`:
- Load existing `.vscode/mcp.json` (empty `{}` if absent).
- Add/overwrite entries under `servers` for Spawn-owned server names.
- Merge `inputs` array: add new input entries (by `id`); do not duplicate.
- Write back with `json.dumps(indent=2)`.

Merging strategy for `remove_mcp`:
- Remove entries from `servers` by name.
- Remove input entries whose `id` matches a Spawn-generated id for removed servers.
- Write back.

Input `id` derivation: `"{server-name}-{env-var-lower-kebab}"` e.g. `"spectask-token"` for
server `spectask-search`, var `SPECTASK_TOKEN`.

### Agent ignore

`add_agent_ignore` and `remove_agent_ignore` both emit `warnings.warn` and return without
mutating any file. GitHub Copilot content exclusion does not apply to IDE Agent mode.

### Entry point

Write managed HTML block to **both**:
1. `.github/copilot-instructions.md`
2. `AGENTS.md` (root)

Both use `rewrite_managed_block`. Both paths returned/logged.

```python
def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
    ep1 = target_root / ".github" / "copilot-instructions.md"
    ep2 = target_root / "AGENTS.md"
    rewrite_managed_block(ep1, prompt)
    rewrite_managed_block(ep2, prompt)
    return str(ep1.relative_to(target_root))
```

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

class GitHubCopilotAdapter(IdeAdapter):
    key = "github-copilot"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".github").exists() or (target_root / ".vscode").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="unsupported",
                entry_point="copilot-instructions",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".github" / "skills" / name
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
        mcp_path = target_root / ".vscode" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("servers", {})
        data.setdefault("inputs", [])
        rendered_names = []
        for server in normalized_mcp.servers:
            entry, new_inputs = _build_vscode_mcp_entry(server)
            data["servers"][server.name] = entry
            existing_ids = {inp["id"] for inp in data["inputs"]}
            for inp in new_inputs:
                if inp["id"] not in existing_ids:
                    data["inputs"].append(inp)
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        mcp_path = target_root / ".vscode" / "mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        removed_input_ids: set[str] = set()
        for name in rendered_mcp_names:
            data.get("servers", {}).pop(name, None)
            # collect derived input ids for this server
            # id pattern: "{server-name}-{env-var-lower-kebab}"
            # We remove any input whose id starts with the server name prefix
            removed_input_ids.add(name)
        data["inputs"] = [
            inp for inp in data.get("inputs", [])
            if not any(inp["id"].startswith(name + "-") or inp["id"] == name
                       for name in rendered_mcp_names)
        ]
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        warnings.warn(
            "github-copilot: agent ignore is unsupported; "
            "GitHub Copilot content exclusion does not apply to IDE Agent mode"
        )

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        warnings.warn("github-copilot: agent ignore is unsupported")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep1 = target_root / ".github" / "copilot-instructions.md"
        ep2 = target_root / "AGENTS.md"
        rewrite_managed_block(ep1, prompt)
        rewrite_managed_block(ep2, prompt)
        return str(ep1.relative_to(target_root))

register(GitHubCopilotAdapter())
```

### VS Code MCP entry builder

```python
def _build_vscode_mcp_entry(server) -> tuple[dict, list[dict]]:
    """Returns (server_entry_dict, inputs_list)."""
    transport = server.transport
    entry: dict = {}
    inputs: list[dict] = []

    if transport.type == "stdio":
        entry["type"] = "stdio"
        entry["command"] = transport.command
        entry["args"] = transport.args
    else:
        entry["type"] = transport.type
        entry["url"] = transport.url

    if server.env:
        env_dict: dict = {}
        for var_name, var in server.env.items():
            if var.secret:
                input_id = f"{server.name}-{var_name.lower().replace('_', '-')}"
                env_dict[var_name] = f"${{input:{input_id}}}"
                inputs.append({
                    "id": input_id,
                    "type": "promptString",
                    "description": var_name,
                    "password": True,
                })
            else:
                env_dict[var_name] = var.value or f"${{{var_name}}}"
        entry["env"] = env_dict

    return entry, inputs
```

## Tests — `tests/ide/test_github_copilot.py`

All tests use `tmp_path` fixture.

- `test_detect_with_github_dir` — `.github/` present → `used_in_repo=True`
- `test_detect_with_vscode_dir` — `.vscode/` present → `used_in_repo=True`
- `test_detect_neither` → `used_in_repo=False`
- `test_add_skills_creates_under_github` — path is `.github/skills/{name}/SKILL.md`
- `test_add_skills_warns_on_overwrite`
- `test_remove_skills_deletes_file`
- `test_add_mcp_creates_vscode_mcp_json` — file is `.vscode/mcp.json`
- `test_add_mcp_uses_servers_key_not_mcp_servers` — top-level key is `servers`, not `mcpServers`
- `test_add_mcp_secret_generates_input` — `inputs` entry created; env references `${input:id}`
- `test_add_mcp_merges_inputs_no_duplicate` — adding same server twice doesn't duplicate input
- `test_remove_mcp_removes_server_and_inputs` — `servers` entry and matching `inputs` removed
- `test_add_agent_ignore_warns`
- `test_remove_agent_ignore_warns`
- `test_rewrite_entry_point_writes_copilot_instructions` — `.github/copilot-instructions.md` updated
- `test_rewrite_entry_point_also_writes_agents_md` — `AGENTS.md` also updated
- `test_rewrite_entry_point_returns_copilot_path`
