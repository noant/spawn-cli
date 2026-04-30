linked task: none

## Idea (informal)

**Full IDE adapters** for targets that were previously represented only by **`StubAdapter`** in the registry: **qoder**, **qwen-code**, **aider**, **zed**, **devin**.

Each needs a module under `src/spawn_cli/ide/` (pattern: existing `cursor.py`, `codex.py`, …), **`IdeAdapter`** implementation covering `detect`, skills, MCP, agent ignore, entry point, and registration at import, plus tests mirroring peer adapters.

**`CANONICAL_IDE_KEYS`** in `spawn_cli.core.low_level` must be extended in **design-approved order** (restore relative ordering vs. the old 11-key list or follow `spec/design/ide-adapters.md`). **Aliases**: reintroduce `qwen` → `qwen-code` in `registry.ALIASES` when `qwen-code` returns.

**Reference:** matrix and paths for each IDE in `spec/design/ide-adapters.md` (skill dirs, MCP file, ignore, entry point).

## Design questions (for `spectask-create`)

- One spectask per IDE vs one task for all five.
- Order of keys when appending to `CANONICAL_IDE_KEYS`.
- Whether **`StubAdapter`** stays test-only or is removed once no stubs remain.

When you promote this seed, run **`spectask-create`**; **Step 1** and **Step 7** item **4** (seed ↔ overview linking) apply there.
