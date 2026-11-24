# Step 4: Tests and validation coverage

Canonical checklist: **`overview.md`**, **Implementation details**, **Regression tests**.

## Goal
Prevent regressions: parsing/proxy-flag validation, **`mcp_stdio`** happy-path and failures, adapters emit stable payloads for **`spawn_stdio_proxy: true`** servers.

## Approach
1. **Unit**: **`NormalizedMcp`** parse with / without **`spawn_stdio_proxy`**; **`extension_check`** rejects bad combinations (**proxy + non-stdio**).
2. **CLI/integration**: **`subprocess`** or **`CliRunner`** (if pytest supports) **with** mocked inner server **or** **`echo`**-style shim—only assert Spawn wires streams where feasible without full MCP (**document** pragmatic limits).
3. **Golden / snapshot**: per-adapter string fragments for **`mcp_stdio`** substring and **absence** of raw **`uvx`** when **`proxy`** enabled.
4. **Negative**: unknown extension/name, **`proxy`** false server invoked via **`mcp_stdio`** -> **`SpawnError`**.
5. **Cross-platform filenames**: unaffected—tests run on CI OS only; avoid OS-specific assertions except **stem** normalization already tested elsewhere (**reuse fixtures** **`conftest`**).

## Affected files
- **`tests/core/test_*mcp*`** (existing or **new test file** beside **`test_low_level` / `test_high_level`**).

## Notes
Step **7** (**design**) is **outside** this subtask (**per `spec/main.md`**); nonetheless list expected doc deltas in **`overview.md`** (**already done**) for **`spectask-design`**.
