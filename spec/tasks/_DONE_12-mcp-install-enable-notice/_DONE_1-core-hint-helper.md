# Step 1: Core hint helper and wiring

## Goal

Add a reusable stdout line (or two) and wire it so **any** IDE gets the notice whenever `refresh_mcp` actually persists at least one server for that IDE (non-empty rendered names).

## Approach

1. Implement `_emit_mcp_installed_enable_notice(ide_key: str | None)` (or placement entirely inside `refresh_mcp` without exporting) that prints the **canonical line** from overview **Message contract** verbatim to stdout (see **Canonical stdout line (exact)**).

2. **Primary hook:** end of **`refresh_mcp`** in `spawn_cli/core/high_level.py`: after **`save_mcp_rendered`**, if `new_names` is non-empty → emit once. Covers install/update/reinstall/extension refresh/build for Cursor, Claude Code, Codex, GitHub Copilot, Gemini CLI, etc., **without** special-casing per IDE title.

3. **`add_ide`:** consolidate emissions so registering a new IDE does not print duplicate lines for **each** extension when many extensions expose MCP — e.g. single notice after loops if **any** refresh in that `add_ide` run produced non-empty `new_names`, **or** rely on per-`refresh_mcp` emissions only if consolidation is costly (document tradeoff in commit; prefer one line per `add_ide`).

4. Do not emit when `add_mcp` returns an empty list (Windsurf and any future no-op adapter).

## Affected files (expected)

- `src/spawn_cli/core/high_level.py` — `refresh_mcp` + optional tweak to `add_ide`.

## Code examples / constraints

```python
new_names = adapter.add_mcp(target_root, nm)
ll.save_mcp_rendered(target_root, ide, extension, new_names)
if new_names:
    print(
        "MCP was merged for this workspace; you may need to press Enable in your IDE MCP UI."
    )

```
