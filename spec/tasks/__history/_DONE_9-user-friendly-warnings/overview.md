# 9: User-friendly CLI warnings (no Python warning banner)

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

When the `spawn` CLI emits recoverable warnings (including static file overwrite during install), stderr shows a short, readable line without Python’s default `path:line: WarningClass:` prefix.

## Design overview

- Affected modules: CLI entry (`spawn_cli.cli.main` or a tiny helper imported first), optionally `spawn_cli.core.errors` or new `spawn_cli.io.warnings_fmt` for the `showwarning` hook; all `warnings.warn(..., SpawnWarning)` call sites for message wording; any other user-facing `warnings.warn` paths we choose to align (IDE overwrite, etc.).
- Data flow changes: once at process start, register a `warnings.showwarning` implementation that handles `SpawnWarning` (and optionally subclasses) by printing a single line to stderr; leave non-Spawn warnings on the default formatting unless we explicitly widen scope.
- Integration points: subprocess or `warnings.catch_warnings` tests asserting stderr does not contain `.py:` line markers or `SpawnWarning` for covered cases.

## Before → After

### Before

- Example: `D:\...\download.py:344: SpawnWarning: overwriting existing static file (Spawn-managed install): spec/main.md`
- Users see file paths inside the Python package and the exception class name.

### After

- Example: `spawn: warning: Replacing existing file from extension (static): spec/main.md` (exact copy to be agreed in implementation; must stay ASCII, English, concise.)
- No Python source path, no line number, no `UserWarning` / `SpawnWarning` label in the banner.

## Details

- **Install point:** Register the hook at the very beginning of `main()` (before `parse_args` / dispatch), so any early code path can benefit. Use `warnings.showwarning` assignment; preserve and chain to the previous handler for categories we do not rewrite (if required for test isolation, expose a small `install_*` / `reset_*` pair used only from tests).
- **Format contract:** One line to stderr; prefix `spawn: warning:` then the message body. Message body must not duplicate the prefix. No stack trace for normal warnings.
- **Category:** At minimum, format warnings whose category is `SpawnWarning`. If IDE modules use plain `UserWarning` for the same audience, either pass `SpawnWarning` there or extend the hook with a narrow rule document in this task (prefer using `SpawnWarning` for consistency).
- **Message refresh:** Review each `SpawnWarning` message (and aligned call sites): plain English, describe what happened and what the user might care about, avoid internal jargon like “Spawn-managed install” unless shortened for clarity.
- **Library vs CLI:** Document that friendly formatting applies when running the CLI; programmatic importers keep standard warning behavior unless they opt into the helper (optional note in code docstring only if needed).
- **Tests:** Add or extend tests to trigger a `SpawnWarning` via public API / subprocess and assert stderr matches the friendly pattern and does not contain `SpawnWarning:` or a substring like `download.py:`.

## Execution Scheme

> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-warning-format-hook` → step `_DONE_2-messages-and-tests`
