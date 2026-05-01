# Step 2: Tests for MCP install / Enable notice

## Goal

Assert stdout contains the MCP “installed / Enable” line when MCP merge returns non-empty server names for a project-backed IDE adapter, and stays silent when the adapter does not persist MCP.

## Approach

1. Use pytest **`capsys`** with small tmp repos (`spawn init`, register at least one IDE, install extension stub with **`spawn/.extend/&lt;name&gt;/mcp.json`** matching existing test fixtures).

2. Cases minimally:
   - **Positive:** e.g. **Cursor** (or Claude Code — any adapter with **`mcp=\"project\"`** and non-empty **`add_mcp`** return) — stdout contains the **exact** canonical line from overview **Canonical stdout line (exact)** (optionally assert the full line plus single trailing newline).
   - **Silent:** **Windsurf** (adapter returns **`[]`** from **`add_mcp`**) plus MCP extension → no MCP-enable notice stdout (warnings may exist separately).

3. Optionally add **second IDE** registration in another test to prove the same substring logic applies without cursor-specific branching.

## Affected files (expected)

- `tests/` under `tests/ide/` and/or `tests/core/` beside existing MCP tests.
