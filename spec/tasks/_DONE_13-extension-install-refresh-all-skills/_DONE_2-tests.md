# Step 2: Tests

## Goal
Lock in cross-extension skill metadata behavior: when a second extension adds a `globalRead: required` (or `auto` appearing in contextual lists) file, skills from the **first** extension gain that read in rendered output after install; when the second extension is removed, the first extension’s skills drop it.

## Approach
1. Add integration-style tests under `tests/core/` (e.g. extend `test_high_level.py` or add a focused module) using `tmp_path`, `spawn_cli.core.low_level.init`, and a stub or lightweight IDE adapter if the suite already has patterns for fake IDEs.
2. **Fixture**: Two minimal extensions under `spawn/.extend/` with distinct names, distinct skills, and non-conflicting normalized skill names. Extension A: one skill; Extension B: at least one file in `extsrc/files/` marked `globalRead: required` (and `localRead` as needed so the file is merged into A’s skill metadata per existing rules).
3. **Assert**: After `install_extension` for B in a repo that already has A, read rendered skill content or metadata for A’s skill and assert the new global mandatory file is listed (match the same mechanism other tests use—e.g. rendered markdown substring or `SkillMetadata` via a test hook).
4. **Assert**: After `remove_extension(B)`, repeat for A’s skill and assert B’s global file is no longer in mandatory reads.
5. Cover the `_refresh_extension_core` path without exercising full git download if tests already patch `download_extension` to drop a prefab tree—otherwise use the real install path from staged folders per existing `test_download` patterns.

## Affected files
- `tests/core/test_high_level.py` and/or new test module alongside existing core tests.
