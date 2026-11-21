# 2: Tests

## Goal
Lock conditional warning semantics for extension-driven refresh and tightened `add_ide` guards.

## Approach
1. Extend `tests/core/test_high_level.py` (preferred) mirroring `_refresh_extension_core`/`add_ide` fixtures already used elsewhere; patch `warnings.warn` and assert call counts/message substrings (`SpawnWarning` category checks optional if existing style omits categories).
2. Cover at least three scenarios via minimal tmp repositories + stubs (pin **`list_ides` to one IDE** unless the test asserts warning count scales with IDE list length):
   - `_refresh_extension_core` with MCP-only extension on an IDE stub whose `capabilities.mcp == "unsupported"` triggers MCP warning exactly once while `skills` untouched (no warnings) when extensions lack skill files.
   - `_refresh_extension_core` with skill-only metadata on IDE stub whose `capabilities.skills == "unsupported"` triggers skills warning exactly once without MCP payloads (`mcp.json` absent or `.servers` empty).
   - `add_ide` with zero extensions installed emits **no** capability warnings even if capabilities degrade.
3. Optional fast follow inside this step if trivial: regression ensuring `refresh_extension_for_ide` mirrors `_refresh_extension_core` MCP scoping versus skills aggregate boolean.

## Affected files
- `tests/core/test_high_level.py` (possibly shared fixtures under `tests/core/conftest.py` if already patterned)

## Constraints
- Keep tests deterministic: patch IDE adapters or reuse existing registry fixtures so no dependency on Cursor/Windsurf on-disk layouts.
