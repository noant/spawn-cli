# 3: Block-style YAML serialization everywhere

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
Every YAML write path in this repository (metadata files, `spawn/navigation.yaml`, CLI YAML output, and test dump helpers) must serialize **only in block style** for structured nodes—no flow collection forms such as `{ … }` or `[ … ]` for nested mappings and sequences.

## Design overview
- **Affected modules:**
  - `src/spawn_cli/io/yaml_io.py` — shared configuration of `ruamel.yaml.YAML` before `dump` (used by `save_yaml`; expose a small helper so other modules and tests can reuse the same policy).
  - `src/spawn_cli/core/low_level.py` — `save_extension_navigation`: apply the same policy before `YAML(typ="rt").dump(...)` while preserving round-trip comment behavior where `typ="rt"` is already used.
  - `src/spawn_cli/cli.py` — `_print_yaml`: same policy for stdout.
  - `tests/core/test_low_level.py`, `tests/core/test_download.py`, `tests/core/test_high_level.py` — module-level `YAML(typ="safe")` instances used in local `_write_yaml` helpers must apply the shared configuration after constructing the instance so tests match production output.
  - `tests/io/test_yaml_io.py` — add a regression test that representative nested structures (list of `{path, description}` dicts) do not emit flow list items (`- {`).
- **Data flow changes:** Parsed data semantics unchanged; only serialized YAML representation (block mappings/sequences wherever meaningful).
- **Integration points:** Every code path that calls `YAML(...).dump` or `save_yaml` must use the shared block-style configuration; loaders remain unchanged.

## Before → After

### Before
- Ruamel defaults may emit flow style for nested mappings (e.g. `files:` entries in `spawn/navigation.yaml` as `- {description: …, path: …}`), with awkward line wraps for review.

### After
- Spawn-generated YAML for non-trivial trees uses consistent block indentation (e.g. `path` / `description` on dedicated lines); same convention for persisted files and CLI YAML printing.

## Details

### Recorded clarifications / defaults
- **Stack:** Continue using only `ruamel.yaml`; keep `YAML(typ="rt")` for navigation round-trip where it already exists.
- **Dumper settings:** Set `default_flow_style = False` on every YAML instance that performs `dump` in-repo; optionally raise `width` (e.g. `4096`) to reduce gratuitous wrapping without changing semantic structure.
- **Empty mappings:** A bare `{}` for an empty dict in edge cases is acceptable; the requirement applies to non-empty trees written as project/config/navigation YAML.
- **Test dumpers:** Use the same configuration as production writes so assertions reflect on-disk reality.
- **Regression:** At least one test ensures a nested “navigation-like” blob serializes without a flow-mapping list stem (`- {`) and includes block markers such as `- path:`.

### Target layout example (navigation `files`)

```yaml
files:
  - path: spec/main.md
    description: Short line.
```

Not mixed/flow `{ path: …, description: … }` for the same logical content.
