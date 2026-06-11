# 26: OpenCode IDE Adapter

## Source seed
- Path: none

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [ ] Code review passed
- [ ] Design documents updated

## Goal
Add a fully correct OpenCode IDE adapter to Spawn, covering skills, MCP, entry point, finalization, and design doc update.

## Design overview
- Affected modules: `src/spawn_cli/ide/opencode.py`, `src/spawn_cli/ide/_vacancy.py`, `src/spawn_cli/ide/__init__.py`, `src/spawn_cli/core/low_level.py`, `tests/ide/test_opencode.py`, `tests/ide/test_registry.py`, `spec/design/ide-adapters.md`
- Data flow changes: new IDE key `opencode` added to `CANONICAL_IDE_KEYS`; adapter writes skills to `.opencode/skills/{name}/SKILL.md`, MCP to `opencode.json` at project root; finalization removes both targets cleanly
- Integration points: adapter registry (canonical key order), vacancy cleanup, design doc matrix

## Before -> After

### Before
- `opencode` is absent from `CANONICAL_IDE_KEYS`.
- `OpencodeAdapter` is imported and registered, but has two bugs: constant names use `OPENSEA_` prefix (typo for `OPENCODE_`), and `add_skills` renders flat `.opencode/skills/{name}.md` instead of the required subdirectory `.opencode/skills/{name}/SKILL.md`.
- `__init__.py` exports `OpencodeAdapter` twice in `__all__` (duplicate entry).
- `finalize_opencode_repo` in `_vacancy.py` is incomplete: handles only flat skill files, missing `opencode.json` cleanup, missing `.opencode/` dir removal; `opencode_config_json_mcp_is_empty` helper does not exist yet.
- `spec/design/ide-adapters.md` adapter matrix and key list do not mention opencode.

### After
- `opencode` is in `CANONICAL_IDE_KEYS`; `OpencodeAdapter` registered.
- Skills rendered to `.opencode/skills/{name}/SKILL.md` (subdirectory per skill, matching the opencode skills spec).
- MCP merged into `opencode.json` at project root under `"mcp"` key; `"type": "local"` for stdio, `"type": "remote"` for HTTP/SSE; env vars under `"env"` key.
- Entry point: `AGENTS.md` (managed block).
- Agent ignore: unsupported (warns).
- `finalize_opencode_repo`: cleans `opencode.json` when `mcp` section is empty and no other user content present, prunes empty `.opencode/skills/` subdirs, removes `.opencode/` dir when entirely empty.
- `ide-adapters.md` updated: opencode added to key list, matrix row, and entry-point table.

## Details

### OpenCode Config Locations
- Project config: `opencode.json` at project root (highest precedence).
- Skills: `.opencode/skills/{name}/SKILL.md` (project-level) and `~/.config/opencode/skills/{name}/SKILL.md` (global).
- Entry point: `AGENTS.md` at project root; `CLAUDE.md` is a fallback (opencode also reads it).
- Agent ignore: not supported as a dedicated file; Spawn warns.

### MCP Shape in opencode.json
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["uvx", "my-mcp"],
      "env": { "TOKEN": "${TOKEN}" },
      "enabled": true
    }
  }
}
```
For HTTP/SSE:
```json
{
  "mcp": {
    "server-name": {
      "type": "remote",
      "url": "https://example.com/mcp",
      "enabled": true
    }
  }
}
```

### Skills Layout (Subdirectory per skill)
```
.opencode/
  skills/
    spectask-execute/
      SKILL.md
    mempalace-search/
      SKILL.md
```
`SKILL.md` uses the common Markdown skill shape (frontmatter + body + Hints + Mandatory reads + Contextual reads).

### Rendered Path Format
`{"skill": "<name>", "path": ".opencode/skills/<name>/SKILL.md"}`

### finalize_opencode_repo Cleanup Rules
1. Unlink `opencode.json` if the only meaningful content is an empty-or-absent `mcp` section (possibly alongside `$schema`).
2. Delete each `SKILL.md` found under `.opencode/skills/*/`, then remove empty skill subdirs.
3. Prune the `skills/` dir if empty; remove `.opencode/` dir entirely if empty.

### Detect Signals
`used_in_repo=True` when `.opencode/` dir or `opencode.json` exists at the target root.

## Execution Scheme
> Each step id is the subtask filename.
> MANDATORY! Each step is executed by a dedicated subagent. Do NOT implement inline. No exceptions.
- Phase 1 (sequential): step 1-adapter-fix -> step 2-ide-adapters-doc
