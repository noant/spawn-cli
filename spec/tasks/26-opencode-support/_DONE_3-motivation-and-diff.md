# Step 3: OpenCode Support Motivation & Cursor Implementation Comparison

## Goal
Document the architectural motivation for OpenCode adapter design and show concrete implementation differences vs Cursor.

## Why OpenCode Support Exists

OpenCode is a CLI-based AI coding assistant that reads project-level configuration from `opencode.json` at the repository root. Unlike Cursor (which uses a `.cursor/` directory), OpenCode centralizes MCP, agent ignore, and schema metadata in a single JSON file. Spawn needs to write MCP servers and agent ignore globs into this format so extensions work seamlessly in OpenCode environments.

## Key Architectural Difference: `"native"` vs `"project"` Agent Ignore

The `agent_ignore` capability drives how Spawn manages ignore lists:

| Capability | IDE | Storage | Mechanism |
|------------|-----|---------|-----------|
| `"native"` | Cursor, Windsurf, Gemini CLI | Text file (`.cursorignore`, `.codeiumignore`, `.geminiignore`) | Spawn writes managed regions (`# spawn:core:start/end`, `# spawn:ext:start/end`) into the file |
| `"project"` | OpenCode | JSON config (`opencode.json` → `watcher.ignore`) | Spawn maintains a flat list; `high_level.py` computes diff and calls `add/remove_agent_ignore` |

### Why Regions Exist for Native Mode

Cursor's `.cursorignore` is a plain text file that may contain user-defined globs alongside Spawn-managed globs. To avoid conflicts:

1. **`rewrite_core_agent_ignore`** writes core Spawn globs into a `# spawn:core:start` / `# spawn:core:end` region
2. **`rewrite_extension_agent_ignore`** writes extension globs into a `# spawn:ext:start` / `# spawn:ext:end` region
3. These regions are independently refreshable — core and extension globs can be updated without touching each other

### Why Regions Aren't Needed for Project Mode

OpenCode's `watcher.ignore` is a JSON array. There's no risk of conflicting with user text parsing. `high_level.py` handles this via `_sync_project_agent_ignore_permissions()`:

```python
def refresh_core_agent_ignore(...):
    if cap == "native":
        adapter.rewrite_core_agent_ignore(target_root, core)   # text file regions
    elif cap == "project":
        _sync_project_agent_ignore_permissions(target_root, ide)  # flat list sync

def refresh_extension_agent_ignore(...):
    if cap == "native":
        adapter.rewrite_extension_agent_ignore(target_root, ext)  # text file regions
    elif cap == "project":
        _sync_project_agent_ignore_permissions(target_root, ide)  # flat list sync
```

The `"project"` codepath never calls `rewrite_core/extension_agent_ignore` — it uses `add_agent_ignore` / `remove_agent_ignore` instead, which OpenCode implements.

## OpenCode vs Cursor: Implementation Comparison

### Detection

| Aspect | Cursor | OpenCode |
|--------|--------|----------|
| Signal | `.cursor/` directory exists | `.opencode/` dir OR `opencode.json` exists |
| `agent_ignore` capability | `"native"` | `"project"` |

```python
# Cursor
def detect(self, target_root: Path) -> DetectResult:
    used = (target_root / ".cursor").exists()
    return DetectResult(used_in_repo=used, capabilities=IdeCapabilities(
        skills="native", mcp="project", agent_ignore="native", entry_point="agents-md",
    ))

# OpenCode
def detect(self, target_root: Path) -> DetectResult:
    used = (target_root / ".opencode").exists() or (target_root / OPENCODE_CONFIG_JSON_FILENAME).exists()
    return DetectResult(used_in_repo=used, capabilities=IdeCapabilities(
        skills="native", mcp="project", agent_ignore="project", entry_point="agents-md",
    ))
```

### Skills

Both use identical subdirectory-per-skill layout, differing only in root directory:

| Cursor | OpenCode |
|--------|----------|
| `.cursor/skills/{name}/SKILL.md` | `.opencode/skills/{name}/SKILL.md` |

Implementation is identical except for the path prefix.

### MCP Configuration

| Aspect | Cursor | OpenCode |
|--------|--------|----------|
| File | `.cursor/mcp.json` | `opencode.json` (repo root) |
| Key | `mcpServers` | `mcp` |
| Schema | None | `$schema: "https://opencode.ai/config.json"` |
| Stdio entry | `{"command": "spawn", "args": [...]}` | `{"type": "local", "command": ["spawn", ...], "enabled": true}` |
| HTTP entry | `{"type": "streamable-http", "url": "..."}` | `{"type": "remote", "url": "...", "enabled": true}` |
| Env key | `env` | `environment` |
| Cleanup | Generic `.cursor` dir prune | Custom `opencode.json` emptiness check |

```python
# Cursor MCP entry (flat format)
def _build_mcp_server_entry(server: McpServer) -> dict:
    if transport.type == "stdio":
        entry = {"command": "spawn", "args": mcp_stdio_argv(...)}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": transport.type, "url": transport.url}
    if server.env:
        entry["env"] = {...}
    return entry

# OpenCode MCP entry (typed format)
def _build_opencode_mcp_entry(server: McpServer) -> dict:
    if transport.type == "stdio":
        entry = {"type": "local", "command": cmd, "enabled": True}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": "remote", "url": transport.url or "", "enabled": True}
    if server.env:
        entry["environment"] = {...}
    return entry
```

### Agent Ignore

| Aspect | Cursor | OpenCode |
|--------|--------|----------|
| File | `.cursorignore` (text) | `opencode.json` → `watcher.ignore` (JSON array) |
| `add_agent_ignore` | `rewrite_ignore_block()` — manages `# spawn:start/end` region | JSON read-modify-write with dedup |
| `remove_agent_ignore` | `remove_ignore_block()` — drops matching lines from region | JSON filter with cleanup of empty keys |
| `rewrite_core_agent_ignore` | ✅ `rewrite_core_agent_ignore_region()` | No-op (not needed for `"project"` mode) |
| `rewrite_extension_agent_ignore` | ✅ `rewrite_extension_agent_ignore_region()` | No-op (not needed for `"project"` mode) |
| `clear_spawn_agent_ignore` | `clear_split_agent_ignore_file()` — drops both core/ext regions | Reuses `remove_agent_ignore` with all current globs |

```python
# Cursor: text-file region management
def add_agent_ignore(self, target_root, globs):
    rewrite_ignore_block(target_root / ".cursorignore", globs)

def rewrite_core_agent_ignore(self, target_root, globs):
    rewrite_core_agent_ignore_region(target_root / ".cursorignore", globs)

# OpenCode: JSON flat list
def add_agent_ignore(self, target_root, globs):
    config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
    data = json.loads(config_path.read_text(encoding="utf-8"))
    ignore_list = data.setdefault("watcher", {}).setdefault("ignore", [])
    existing = set(ignore_list)
    for g in globs:
        if g not in existing:
            ignore_list.append(g)
            existing.add(g)
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

### Entry Point

Both write `AGENTS.md` with identical managed-block format. The only difference is return value formatting:

| Cursor | OpenCode |
|--------|----------|
| `str(ep.relative_to(target_root))` | `ep.relative_to(target_root).as_posix()` |

### Finalization

| Cursor | OpenCode |
|--------|----------|
| `_vac.finalize_standard_dotdir_skills_and_mcp(target_root, ".cursor", allow_delete_entire=True)` | `_vac.finalize_opencode_repo(target_root)` — custom logic that checks `opencode.json` emptiness and prunes `.opencode/skills/` subdirs |

## Summary Table

| Feature | Cursor | OpenCode | Notes |
|---------|--------|----------|-------|
| Skills path | `.cursor/skills/` | `.opencode/skills/` | Same layout, different root |
| MCP file | `.cursor/mcp.json` | `opencode.json` | Different schemas |
| MCP format | `mcpServers` (flat) | `mcp` (typed with `type` field) | Structural difference |
| Agent ignore | `.cursorignore` (text regions) | `watcher.ignore` (JSON array) | Architectural difference |
| Core/ext regions | ✅ Supported | N/A | Not needed for JSON-based config |
| Entry point | `AGENTS.md` | `AGENTS.md` | Identical |
| Detection | `.cursor/` dir | `.opencode/` dir or `opencode.json` | OpenCode has broader detection |
| Finalization | Generic dotdir cleanup | Custom `opencode.json` + `.opencode/` cleanup | IDE-specific logic |
