# 22: Cross-platform extension MCP via extsrc/mcp platform files

## Source seed
- Path: none

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] Design documents updated

## Goal
Author extension MCP once per operating system family using three JSON files under `extsrc/mcp/`, with install-time copy of all three and runtime merge driven by host OS detection, while `spawn extension init` (and `from-rules`) scaffold those files empty.

## Design overview
- Affected modules: `spawn_cli.core.low_level` (`list_mcp` and any shared path helpers); `spawn_cli.core.download` (`_candidate_mcp_server_names`, staging checks); `spawn_cli.core.high_level` (`extension_init`, `extension_check`, `extension_from_rules`); `spawn_cli.cli` (help strings mentioning MCP paths); tests under `tests/core/`.
- Affected documentation (Step 7): `spec/design/extension-author-guide.md` must describe the `extsrc/mcp/*.json` layout, per-OS authoring rules, scaffold behavior, and that root `mcp.json` is unsupported; align other design refs (`hla.md`, `utility-method-flows.md`, `data-structure.md`) as needed.
- Data flow changes: Installed layout uses only `spawn/.extend/{extension}/mcp/{windows,linux,macos}.json` (copied from `extsrc/mcp/`). `list_mcp` loads the JSON file for the current host. Root-level `mcp.json` next to the extension tree is **not** supported: never read for merge; `extension check` flags it so authors remove or migrate content into `mcp/*.json`.
- Integration points: IDE adapters and `refresh_mcp` stay unchanged; they still consume `NormalizedMcp` from `list_mcp`. Extension packaging (`_copy_extsrc_tree`) copies the full `extsrc` tree including `mcp/`.

## Before → After
### Before
- Authors place one `extsrc/mcp.json`; it is copied to `spawn/.extend/{id}/mcp.json`. MCP commands/paths cannot differ cleanly by OS in one file.
- `spawn extension init` does not create any MCP files.
### After
- Authors maintain `extsrc/mcp/windows.json`, `extsrc/mcp/linux.json`, and `extsrc/mcp/macos.json` (object with top-level `servers` array; same server object shape as before). Adding a server requires defining it in all three files (names and cardinality aligned; per-OS transport fields may differ).
- On install, all three files are copied under `spawn/.extend/{id}/mcp/`. At runtime, `list_mcp` selects the file for the detected OS (`win32` → `windows`, `linux` → `linux`, `darwin` → `macos`).
- `spawn extension init` and `extension_from_rules` create `extsrc/mcp/` with the three files present and valid empty documents (`{"servers": []}`).
- Root `mcp.json` (authoring or installed) is obsolete: not loaded; authors must rely solely on `mcp/*.json`.

## Details
- **Filenames (exact)**: `mcp/windows.json`, `mcp/linux.json`, `mcp/macos.json` relative to `extsrc/` and to `spawn/.extend/{extension}/`.
- **JSON schema**: Object with `servers` list of server objects (same shape as historical MCP JSON); paths in errors must name the concrete platform file under `mcp/`.
- **OS detection**: New small helper (e.g. in `spawn_cli.core` or next to `list_mcp`) maps `sys.platform` to one of `windows` | `linux` | `macos`. Unknown platforms: raise `SpawnError` with a clear message (no silent fallback).
- **Authoring validation (`extension_check`)**:
  - **Stray root `mcp.json`**: If `extsrc/mcp.json` exists (root of extsrc, sibling of `mcp/`), warn (non-strict) or error (strict); it must not be used. Same for a root `mcp.json` next to installed `spawn/.extend/{id}/` when running check against that tree, if applicable.
  - Require `extsrc/mcp/` with all three platform files present and parseable (same structural checks as today’s MCP JSON parsing).
  - **Server name alignment**: The set of `name` values in `servers` must be identical across all three files (order-independent). If one file has `servers: []` while another does not, error in strict mode; warn in non-strict.
  - If `mcp/` exists but any of the three files is missing, invalid layout (error in strict; warn otherwise where applicable).
- **Staging / duplicate MCP names** (`_candidate_mcp_server_names`): When using the new layout, collect server names from any one platform file (they are equal by validation) or union with identical-set check; on install, reject duplicates across extensions as today.
- **Scaffold**: `extension_init`: `ensure_dir(extsrc / "mcp")` and write three files with `{"servers": []}` if missing (do not overwrite existing). `extension_from_rules`: after existing layout, same three files if not present.
- **Extension author guide**: In Step 7, update **`spec/design/extension-author-guide.md`** so authors see the canonical MCP story: three platform files under `extsrc/mcp/`, same server names in each file, OS-specific transport fields, empty scaffold from `extension init` / `from-rules`, `extension check` expectations, and explicit note that **`extsrc/mcp.json` is invalid** for new work.
- **CLI**: Update `--strict` help and any user-visible strings to describe only `mcp/*.json` (no root `mcp.json`).
- **Tests**: Platform resolution; `list_mcp` reads only `mcp/{platform}.json`; `extension_check` rejects or warns on root `mcp.json`; name misalignment across platform files; scaffold creates three empty files.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-mcp-resolve.md` → step `2-mcp-validation-staging.md`
- Phase 2 (sequential): step `3-scaffold-cli-tests.md`
- Phase 3 (sequential): step review — inspect all changes, fix inconsistencies
