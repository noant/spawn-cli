# Step 1: Warning format hook

## Goal

Install a `warnings.showwarning` handler when the CLI starts so `SpawnWarning` prints as a single friendly line on stderr.

## Approach

- Add a small function (e.g. `_install_user_warnings()` or module `spawn_cli._warnings_display`) that replaces `warnings.showwarning`, delegates non-`SpawnWarning` categories to the previous handler, and for `SpawnWarning` prints `spawn: warning: {text}` with no filename/lineno/category in the output.
- Call it from the first line of `main()` before parsing arguments.
- If tests need isolation, save/restore the previous `warnings.showwarning` in fixtures or provide an internal reset used only from tests.

## Affected files

- `src/spawn_cli/cli.py` — call site at entry.
- New helper module under `src/spawn_cli/` if logic is non-trivial.

## Code notes

- Use `issubclass(category, SpawnWarning)` if we allow subclasses later.
- Strip trailing newlines from `message` before formatting.
