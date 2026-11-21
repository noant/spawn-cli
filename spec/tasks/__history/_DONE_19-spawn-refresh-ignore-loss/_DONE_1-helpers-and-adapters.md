# Step 1: Helpers and IDE adapters

## Goal
Introduce distinct managed markers and rewrite/partition helpers for **Core** and **Extension** ignore regions; update native-ignore IDE adapters to read/write both regions without relying on empty-globs “delete whole legacy block” during normal refresh.

## Approach
- Add marker constants (e.g. `SPAWN_CORE_IGNORE_START` / `END`, `SPAWN_EXT_IGNORE_START` / `END`) in `spawn_cli.ide._helpers` (or adjacent module used by adapters).
- Implement `rewrite_core_ignore_block(path, globs)` and `rewrite_extension_ignore_block(path, globs)` (or one parameterized `rewrite_spawn_ignore_region(path, kind, globs)`) that preserve user content **outside** both Spawn regions. Handle legacy single `# spawn:start` / `# spawn:end` region: on first rewrite, either migrate split into core+ext or replace with two blocks per agreed rule in overview **Details**.
- Update `cursor`, `windsurf`, `gemini_cli` adapters so `add_agent_ignore` / `remove_agent_ignore` either delegate to the new helpers with the right region, or expose small internal hooks used only by high_level. Keep `registry.py` / `IdeAdapter` protocol consistent with whatever surface high_level needs (or keep adapter entry points stable and move logic into helpers only — prefer minimal breakage).
- Ensure **`remove_ide`** path can strip both regions (adapter or helper entry “remove all spawn ignore regions”).

## Affected files
- `src/spawn_cli/ide/_helpers.py`
- `src/spawn_cli/ide/cursor.py`, `windsurf.py`, `gemini_cli.py`
- `src/spawn_cli/ide/registry.py` if protocol changes
- `tests/ide/` for partition/rewrite behavior

## Deliverable
- Helpers and adapters ready for high_level to call **core** and **ext** refreshes independently.
- Tests for partitioning, rewrite, and legacy migration behavior as agreed.
