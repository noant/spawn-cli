# Step 7: Self Code Review

## Required reading
Before reviewing, read:
- `spec/design/utility.md` — Core Rules, all module sections, Lifecycle Semantics, Rebuild Semantics
- `spec/design/ide-adapters.md` — full document
- `spec/design/data-structure.md` — full document
- `spec/design/extensions.md` — full document
- `spec/design/agentic-flow.md` — full document

## Goal
Inspect all changes from steps 1–6, fix inconsistencies, naming issues, broken contracts, missing imports, and ensure the full codebase is internally consistent.

## Approach
A dedicated subagent reads every implemented file and checks against the spec. Issues are fixed inline. No new features are introduced at this step.

## Checklist

### Cross-cutting concerns
- [ ] All `pathlib.Path` usage consistent (no raw string paths)
- [ ] All type hints present on public functions
- [ ] `SpawnError` vs `SpawnWarning` used correctly per spec rules
- [ ] **Every CLI path** uses `Path.cwd().resolve()` — **no** `--target`
- [ ] **Non-blocking `spawn_lock`** on all commands (including read-only); correct busy message (`utility.md`)
- [ ] **Init guard**: all commands except `spawn init` require existing `spawn/` (**`need init before`**)
- [ ] **Canonical IDE keys**: single `CANONICAL_IDE_KEYS` source; **no** env/config overrides
- [ ] All enum comparisons use `.value` or `==` with `ReadFlag.required` etc.

### Models
- [ ] Field aliases match YAML/JSON keys exactly (hyphens → underscores via alias)
- [ ] `model_config = ConfigDict(populate_by_name=True)` where needed for alias round-trips
- [ ] Optional fields have correct defaults (not `None` where list expected)

### I/O
- [ ] `ensure_dir` called before every `write_text` / `save_yaml` / `save_json`
- [ ] `safe_path` used whenever user-provided paths are resolved against `target_root`
- [ ] YAML round-trip preserves comments where required (ruamel.yaml); **regression test** loads hand-edited `spawn/navigation.yaml` with comments → mutate one non-comment field via `save_extension_navigation` / equivalent → comments still present (`tests/core/test_low_level.py` or dedicated I/O test per `6-tests.md`)

### Low-level core
- [ ] `generate_skills_metadata` deduplication is stable (first description wins)
- [ ] `save_extension_navigation` handles all cases: add/update/remove extension section
- [ ] `save_rules_navigation` emits warning (not error) for missing rule files
- [ ] `push_to_global_gitignore` is idempotent (no duplicate lines)

### High-level core
- [ ] Script runner order correct: before-install → copy → refresh → after-install
- [ ] `before-uninstall` when **configured** is **blocking** on failure; when **omitted**, phase skipped (`extensions.md`)
- [ ] `update_extension` uses **`source.yaml` only** (no new CLI path); install rejects mismatched `source.yaml` identity until remove+re-add (`utility.md`)
- [ ] `update_extension` errors on same/older version before any mutation (in-tree version helper — **no** `packaging`)
- [ ] `extension_check` in strict mode returns errors (not warnings)
- [ ] File materialization respects `mode: artifact` (create-only, no overwrite)
- [ ] Skill/MCP refresh: validate cross-extension name uniqueness **before** remove; write `rendered-*.yaml` only after successful adapter add
- [ ] Rerun refresh after partial failure converges (idempotent repair)

### Download
- [ ] Git/zip staging uses `{target_root}/spawn/.metadata/temp/{operation_id}/`; directory removed in `finally` after each operation
- [ ] `git clone` uses `--depth 1` and `--branch` flag only when branch provided
- [ ] Zip extraction validates that extracted files don't escape temp dir
- [ ] `source.yaml` written after successful copy, not before

### IDE adapters
- [ ] All 6 concrete adapters implement all 7 interface methods
- [ ] All warn-only stub adapters implement all 7 methods (warn + no-op)
- [ ] `add_agent_ignore` returns **`None`** / **`void`** only (`ide-adapters.md`)
- [ ] Managed block regex is DOTALL (entry points may have multiline blocks)
- [ ] Codex TOML: hyphenated server names use quoted keys
- [ ] GitHub Copilot VS Code MCP format uses `servers` (not `mcpServers`)
- [ ] `normalize_skill_name` used for all rendered skill directory names
- [ ] `remove_skills` cleans empty parent dirs

### CLI
- [ ] `Path.cwd().resolve()` is the only repository root — **no** `--target**
- [ ] `SpawnError` caught and printed to stderr with exit code 1
- [ ] **Every** subcommand (including `list-supported-ides`, `extension check`, `build list`) runs under **`spawn_lock`**
- [ ] Git-missing `SpawnError` includes per-OS install hints when a git source operation is requested

### Tests
- [ ] No test writes outside `tmp_path`
- [ ] No test makes network calls (httpx, subprocess git clone patched)
- [ ] All test files have `__init__.py` in their directories
- [ ] `conftest.py` fixtures used consistently
- [ ] Tests for warning paths use `pytest.warns` or check stderr

## Output
After review, update `overview.md` status to mark "Self code review passed" and prompt the user.
