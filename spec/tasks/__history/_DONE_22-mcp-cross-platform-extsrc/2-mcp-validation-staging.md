# Step 2: extension_check and install-time MCP name extraction

## Goal
Validate the three-file MCP layout during `extension check`, and ensure staging duplicate-name detection works with `extsrc/mcp/*.json`.

## Approach
- **extension_check** (`high_level.extension_check`):
  - Detect layout: presence of `extsrc/mcp/` and the three expected filenames.
  - Parse each file; on parse errors, surface same style as current MCP JSON checks.
  - Compare sets of server `name` strings across the three files; on mismatch, warn (default) or raise in `--strict`.
  - If `extsrc/mcp.json` exists, warn or error per strict mode (obsolete file; not loaded).
- **download._candidate_mcp_server_names**:
  - Require the `mcp/` trio under `extsrc` (after scaffold), same as post-init layout; derive names from one platform file once all three parse and name sets match.
  - Do not read `extsrc/mcp.json` for staging / duplicate checks.

## Affected files
- `src/spawn_cli/core/high_level.py`
- `src/spawn_cli/core/download.py`
- Tests under `tests/core/`

## Code notes
- Share parsing/name-set extraction with `list_mcp` where possible to avoid drift (private helper in `low_level` callable from download/check).
