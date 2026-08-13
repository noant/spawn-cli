# Step 2: Update ide-adapters.md for OpenCode

## Goal
Add opencode to `spec/design/ide-adapters.md`: canonical key list, IDE Matrix row, and entry-point table row.

## Approach
Three targeted edits to `spec/design/ide-adapters.md`:
1. Add `opencode` to the Adapter Registry supported names list.
2. Add a row to the IDE Matrix table.
3. Add a row to the Entry point targets table.

## Affected files
- `spec/design/ide-adapters.md` — three insertions

## Code changes (before / after)

### `spec/design/ide-adapters.md` — Supported names list

**Before**
```
- `cursor`
- `codex`
- `claude-code`
- `windsurf`
- `github-copilot`
- `gemini-cli`
```

**After**
```
- `cursor`
- `codex`
- `claude-code`
- `windsurf`
- `github-copilot`
- `gemini-cli`
- `opencode`
```

### `spec/design/ide-adapters.md` — IDE Matrix table, after Gemini CLI row

**Before**
```
| Gemini CLI | `.gemini/skills/{skill}/SKILL.md` | `.gemini/settings.json` `mcpServers` | `.geminiignore` | `GEMINI.md` (unless overridden via `context.fileName`) | Project `.gemini/settings.json` at repo root. (CLI may also merge `.agents/skills/` discovery—outside this column.) |
| Devin | ...
```

**After**
```
| Gemini CLI | `.gemini/skills/{skill}/SKILL.md` | `.gemini/settings.json` `mcpServers` | `.geminiignore` | `GEMINI.md` (unless overridden via `context.fileName`) | Project `.gemini/settings.json` at repo root. (CLI may also merge `.agents/skills/` discovery—outside this column.) |
| OpenCode | `.opencode/skills/{skill}/SKILL.md` | `opencode.json` (repo root) `mcp` | `opencode.json` `watcher.ignore` | `AGENTS.md` | Stdio MCP uses `"type": "local"` + `"command"` array; HTTP/SSE uses `"type": "remote"` + `"url"`. Reads `.claude/skills/` and `.agents/skills/` via compatibility layer. `CLAUDE.md` is a fallback entry point. |
| Devin | ...
```

### `spec/design/ide-adapters.md` — Entry point targets table, after Gemini CLI row

**Before**
```
| Gemini CLI | `GEMINI.md` |
| Devin | `AGENTS.md` |
```

**After**
```
| Gemini CLI | `GEMINI.md` |
| OpenCode | `AGENTS.md` |
| Devin | `AGENTS.md` |
```
