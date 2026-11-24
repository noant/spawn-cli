# Step 1: MCP path resolution and list_mcp

## Goal
Implement host-OS selection of the correct platform MCP JSON file under `spawn/.extend/{extension}/mcp/`. Root `mcp.json` is not read.

## Approach
- Add a helper that maps `sys.platform` to `windows` | `linux` | `macos` for `list_mcp`.
- Change `list_mcp` to resolve only `mcp/{platform}.json` under the extension install root.
  - If `mcp/` is missing: return `NormalizedMcp(servers=[])` (same as today’s empty `load_json` result for a missing file).
  - If `mcp/` exists but `{platform}.json` is missing: `SpawnError` (incomplete platform set).
- Do not read `<extension-root>/mcp.json` under any circumstance.

## Affected files
- `src/spawn_cli/core/low_level.py` (primary)
- Possibly new small module under `src/spawn_cli/core/` if it keeps `low_level` smaller — only if consistent with repo style.

## Code notes
- Reuse `load_json` and existing parsing loop; factor path selection into a private function used only by `list_mcp`.
- Error messages should include the resolved platform file path.
