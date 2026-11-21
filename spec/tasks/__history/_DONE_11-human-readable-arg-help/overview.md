# 11: Human-readable CLI argument help

## Source seed

- Path: none

## Status

- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal

Expose clear English `help` text for every CLI argument (and concise subparser descriptions where missing) so `spawn … --help` is self-explanatory without reading the source.

## Design overview

- Affected modules: `spawn_cli.cli` (`build_parser` only unless a tiny test addition is warranted).
- Data flow changes: none; parsing and dispatch stay the same.
- Integration points: `argparse` only; no new dependencies.

## Before → After

### Before

- Positional arguments appear with bare metavars (`path`, `ides`, `extension_name`, …) and no explanatory line in the Arguments section.
- Several optional flags (`--branch`, `--name`, `--strict`, `--output`) have no description.
- Some intermediate subparsers (`ide`, `extension`, `build`) lack a `description`, so group-level `--help` is sparse.

### After

- Every `add_argument` in `build_parser` has a short, accurate English `help=…` string.
- Parent/leaf subparsers where it improves discoverability carry a one-line English `description=…` (and existing `help=…` for command listing remains or is aligned).
- Optional: tighten `metavar` only where it makes the synopsis clearer without conflicting with semantics (default is fine if metavar already reads well).

## Details

1. **Scope** — Changes limited to [`src/spawn_cli/cli.py`](../../../src/spawn_cli/cli.py) inside `build_parser()`.
2. **Wording** — User-facing CLI strings added in English (aligned with [`spawn/rules/00-general.md`](../../../spawn/rules/00-general.md) for new in-code text).
3. **Content** — Descriptions must match actual behavior implied by `_dispatch*` (e.g. `extension init` scaffold path defaults to `.`; `extension check` validates an extension directory; `--branch` applies to git-sourced installs / build manifests).
4. **Tests** — Existing [`tests/test_cli.py`](../../../tests/test_cli.py) only checks top-level `--help` contains `"spawn"`; extending with a shallow assertion (e.g. `spawn extension add --help` mentions branch or URL) is optional if it reduces regressions without brittle full-text snapshots.

## Clarifications (defaults)

| Topic | Decision |
| --- | --- |
| Localization | English only for new help/description strings |
| Subgroup descriptions | Add where currently empty (`ide`, `extension`, `build`, leaf commands missing one-line summaries) |
