# Step 3: Scaffold empty platform files, CLI strings, tests

## Goal
Ensure new extension scaffolds include empty platform MCP files; update CLI help; add/extend tests for the feature.

## Approach
- **extension_init**: After creating `extsrc` directories, `ensure_dir(extsrc / "mcp")` and write `windows.json`, `linux.json`, `macos.json` with `{"servers": []}` when the files do not exist (init must remain idempotent if rerun).
- **extension_from_rules**: After generating `config.yaml` and dirs, add the same three files if missing.
- **cli.py**: Update help text to describe only `mcp/*.json` (no root `mcp.json`).
- **Tests**:
  - `list_mcp` selects correct file under fake `sys.platform` (patch `sys.platform` or inject platform helper).
  - Root `mcp.json` is ignored by `list_mcp`; optional check that `extension_check` flags stray `extsrc/mcp.json`.
  - `extension_init` creates three empty JSON files.
  - `extension_check` warns or errors on mismatched server names across platform files per `--strict`.

## Affected files
- `src/spawn_cli/core/high_level.py`
- `src/spawn_cli/cli.py`
- `tests/core/test_*.py` (new cases in existing files preferred)

## Code notes
- **Step 7 (design docs)**: **`spec/design/extension-author-guide.md`** is required reading for extension authors — update it in the same task as code (do not defer). Also refresh `spec/design/hla.md`, `utility-method-flows.md`, and `data-structure.md` where they mention `mcp.json` or `list-mcp` paths so they match the `mcp/*.json` layout.
