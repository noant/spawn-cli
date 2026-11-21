# 6: CLI command extension reinstall

IMPORTANT: always use `spawn/navigation.yaml` and `spec/main.md` for rules.

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] HLA updated

## Goal
Add `spawn extension reinstall <extension_name>` to fully uninstall an installed extension and install it again from the source recorded in `source.yaml` (same path and branch as `extension add`).

## Design overview
- **Affected modules:** `src/spawn_cli/core/high_level.py` — new `reinstall_extension`; `src/spawn_cli/cli.py` — subparser `reinstall`, dispatch; `tests/test_cli.py` — CLI wiring test; `tests/core/test_high_level.py` (or new focused test module) — behavior / call-order test with mocks.
- **Data flow:** Read `spawn/.extend/{name}/source.yaml` via existing `dl._load_stored_source`; validate extension is listed; call `remove_extension` then `install_extension` with stored `source.path` and `source.branch`.
- **Integration points:** Reuses uninstall hooks (`remove_extension`) and install path (`install_extension` / `download_extension`) unchanged.

## Before → After

### Before
- No dedicated reinstall; users must `extension remove` then `extension add` with the same URL/path and branch manually.

### After
- `spawn extension reinstall <extension_name>` performs remove + install using recorded source; fails with the same class of errors as `extension update` when `source.yaml` is missing or the extension is not installed.

## Details

### User clarifications (defaults)
- **CLI surface:** Subcommand name `reinstall` under `spawn extension`, one positional argument. Use the same argument naming style as `update`/`remove` (`extension_name` in argparse metadata).
- **Semantics:** Equivalent to `remove_extension(target_root, name)` followed by `install_extension(target_root, stored.source.path, stored.source.branch)`. Must run under the existing repo `spawn_lock` like other extension commands.
- **Preconditions:** Extension must appear in `list_extensions` (i.e. `spawn/.extend/{name}` is a registered install). Must have a valid `source.yaml` (same requirement as `update_extension`); if missing, raise `SpawnError` with message consistent with `no source.yaml for extension {name!r}`.
- **Not installed:** If the extension is not in `list_extensions`, raise `SpawnError` (do not silently no-op; `remove_extension` alone would no-op).
- **Version / identity:** No version check: reinstall always re-fetches from source like a fresh `add` after removal, so older-or-equal semver from remote does not block (unlike `update_extension`).
- **Non-goals:** New flags (`--force`, etc.); changing how `source.yaml` is written; supporting reinstall without `source.yaml`.

### Implementation notes
- Implement `reinstall_extension` in `high_level.py` next to `update_extension` / `remove_extension`; export it in `__all__`.
- Prefer delegating to `remove_extension` and `install_extension` for a single code path with hooks and IDE cleanup preserved.
- **Edge case:** After `remove_extension`, `install_extension` uses the extension `name` from the newly staged `config.yaml`. Document as invariant: directory name passed on the CLI should match the extension `name` in config (same as today for `add`); reinstall does not rename installs.

### Tests
- **CLI:** `main(["extension", "reinstall", "my-ext"])` with `_noop_lock`, patch `hl.reinstall_extension`, assert `(root, "my-ext")`.
- **Core:** With a fixture repo that has `_install_ext`-style tree **plus** a minimal valid `source.yaml` under `spawn/.extend/{name}/`, patch `remove_extension` and `install_extension`; call `reinstall_extension`; assert `remove` called before `install`, and `install` receives stored path and branch. Alternatively assert call order via `MagicMock` side_effects. Cover error path: no `source.yaml` → `SpawnError`. Cover: extension missing from `list_extensions` → `SpawnError`.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-core-reinstall.md` — implement `reinstall_extension` in `high_level.py`
- Phase 2 (sequential): step `_DONE_2-cli-and-tests.md` — CLI subcommand and tests
