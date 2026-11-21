# Step 2: Low-level metadata (extension-only)

## Goal
Persist idempotency for **extension** agent-ignore only; core does not use `agent-ignore.`txt for reconciliation.

## Approach
- Split semantics of `get_agent_ignore_list` / `save_agent_ignore_list` into extension-only storage, or add `get_extension_agent_ignore_list` / `save_extension_agent_ignore_list` and migrate call sites. File path may stay `spawn/.metadata/{ide}/agent-ignore.txt` with **redefined** meaning (extensions only) — document in `data-structure.md` in step 4 / Step 7.
- Add `get_merged_extension_agent_ignore(target_root) -> list[str]` (name as implemented) merging all `spawn/.extend/*/config.yaml` `agent-ignore` with stable dedup order matching current `get_all_agent_ignore` extension slice.
- Ensure `get_core_agent_ignore` remains the single source for the core block; no duplication in the idempotency file.
- Handle migration: if existing `agent-ignore.txt` contains lines that match current core globs, treat them as redundant for ext metadata after one refresh (or strip core lines when saving ext-only).

## Affected files
- `src/spawn_cli/core/low_level.py`
- `tests/core/test_low_level.py` (or adjacent) for metadata shape

## Deliverable
- Low-level API supports ext-only last-rendered list and merged extension computation used by `refresh_extension_agent_ignore`.
