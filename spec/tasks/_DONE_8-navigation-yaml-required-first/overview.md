# 8: Canonical navigation.yaml root key order (read-required first)

IMPORTANT: always use `spawn/navigation.yaml` and `spec/main.md` for rules.

## Status

- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal

On every rewrite of `spawn/navigation.yaml`, the top-level key **`read-required` is always emitted first**, then **`read-contextual`**, so mandatory reads precede contextual ones in the file regardless of key order on input.

## Design overview

- Affected modules: `spawn_cli.core.low_level` — `save_extension_navigation` (ruamel round-trip via `YAML(typ="rt")`), `save_rules_navigation` (`load_yaml` / `save_yaml`).
- Data flow changes: before dumping, normalize only the **order of the two known root keys**; list contents and nested structure semantics stay unchanged.
- Integration points: existing tests in `tests/core/test_low_level.py` (including comment round-trip); add a test for top-level key order (raw text or `list(nav.keys())`) if gaps remain.

## Before → After

### Before

- If `navigation.yaml` lists `read-contextual` before `read-required` (merges, older dumps, or manual edits), `save_extension_navigation` / `save_rules_navigation` can persist that order because dict/CommentedMap preserve insertion order from the loaded file.
- Agents still function, but the file contradicts the convention “required first, then contextual”.

### After

- After any write through those helpers, **`read-required` always appears above `read-contextual`** when both keys exist.
- Merge semantics stay the same (required/contextual dedup for extensions, `spawn/rules/` sync, warnings for missing rule files).
- `save_extension_navigation` round-trip still preserves comments in the scenario covered by `test_navigation_yaml_roundtrip_preserves_comments`.

## Details

- `init()` already creates the file with the correct key order; this task covers **all save paths** for an existing file.
- Model-wise, root keys are `read-required` and `read-contextual` (`NavigationFile`). If unknown top-level keys ever appear, **keep them after the canonical pair** in their prior relative order (do not drop data).
- When reordering with Ruamel, preserve comment attachment and section comments.
- Implement once (e.g. `_ensure_navigation_root_key_order`) and call from every `navigation.yaml` writer in `low_level`.

## Self spec review notes

- Scope: both writers; unknown keys trail after the pair.
- Risk: ruamel comment placement — keep the existing round-trip test green.
