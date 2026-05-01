# 2: CLI strings and utility design doc

## Goal
Align user-facing wording with overwrite semantics.

## Approach
- Update `spawn refresh` argparse `help` and `description` in `spawn_cli.cli` so they state that bundled defaults **replace** `spawn/.core/config.yaml`, not merge with existing patterns.
- Update the `spawn refresh` paragraph in `spec/design/utility.md` to describe the same policy (bundled snapshot only); remove language about appended existing patterns.

## Affected files
- `src/spawn_cli/cli.py`
- `spec/design/utility.md`

## Notes
Step 7 (`spec/design/hla.md`) should briefly mention synced core config semantics if required for consistency after implementation; defer to execute phase if unclear.
