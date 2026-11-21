# Step 3: High-level orchestration, call sites, tests

## Goal
Implement `refresh_core_agent_ignore`, `refresh_extension_agent_ignore`, and compose `refresh_agent_ignore`; replace all duplicate agent-ignore refresh logic; add regression coverage.

## Approach
- **`refresh_core_agent_ignore`:** Read `ll.get_core_agent_ignore`; rewrite **core** region only via adapter/helper.
- **`refresh_extension_agent_ignore`:** Compute merged extension globs; diff against **ext-only** metadata; update **extension** region (no empty-list full wipe bug); persist ext idempotency file.
- **`refresh_agent_ignore`:** Call core then extension (document order). Every current `refresh_agent_ignore` caller keeps calling this orchestrator only.
- **`remove_extension_for_ide`:** Replace combined `old`/`new` `get_all_agent_ignore` / `_agent_ignore_merge_excluding` + adapter diff with: update extension block + ext metadata; **do not** alter core block.
- **`remove_ide`:** Remove both spawn ignore regions and delete ext metadata / IDE metadata dir per existing layout.
- **Tests:** Add regression for “full refresh with unchanged configs leaves both blocks populated”; exercise real ignore rewrite (Cursor adapter or `_helpers`). Cover `remove_extension_for_ide` leaves core globs in file. Run existing suite.

## Affected files
- `src/spawn_cli/core/high_level.py` (and `__all__` exports if public API expands)
- `tests/core/test_high_level.py` (stubs may need updates if adapter methods split)
- `spec/design/data-structure.md`, `utility.md`, `ide-adapters.md` as needed (Step 7 may consolidate with HLA)

## Deliverable
- Single orchestrated path for agent-ignore refresh; removes root cause of empty-diff wiping ignores; documentation and tests updated per spec.
