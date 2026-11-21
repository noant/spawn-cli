# 12: MCP install notice — Enable in IDE (all IDEs)

IMPORTANT: always use `spawn/navigation.yaml` and `spec/main.md` for rules.

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

When an extension contributes MCP servers and Spawn merges them for a registered IDE that persists project MCP, completing the merge prints one concise stdout line that MCP is installed for the project and the user may need to use **Enable** (or an equivalent control) in the IDE’s MCP interface.

## Design overview

- Affected modules: `spawn_cli.core.high_level` (`refresh_mcp` and `add_ide` integration), possibly a small helper module for the fixed message string; IDE adapters unchanged unless a shared guard is needed; tests under `tests/core` and/or `tests/ide`.
- Data flow changes: After a successful MCP merge (`adapter.add_mcp` returns non-empty rendered server names), emit the notice unless the IDE is one that intentionally does **not** write project MCP (today: **Windsurf** returns an empty rendered list — no emission). Any IDE adapter that merges servers and returns rendered names qualifies.
- Integration points: `refresh_mcp` (covers every `_refresh_extension_core` path including install/update/reinstall/extension refresh across all registered IDEs); **`add_ide`** when the newly added IDE refreshes MCP for existing extensions.

## Before → After

### Before

- Merging MCP into repo-local IDE config (.cursor vs .mcp.json vs `.vscode/mcp.json`, etc.) succeeds silently; users may assume MCP is active inside the IDE without toggling MCP.

### After

- Stdout shows one short informational line (ASCII per `spawn/rules/00-general.md`) stating that MCP was installed for the project and that an **Enable** action (or equivalent) in the IDE MCP UI may still be required.

## Details

### Out of scope / non-goals

- Changing MCP JSON merge semantics or adapter file paths.
- Auto-enabling MCP inside any IDE (not available at Spawn layer).
- Broad changes to existing `SpawnWarning` messages except where a call site is shared with the new notice hook.

### When to emit

Emit **whenever** `refresh_mcp` completes with at least one rendered server name returned from `adapter.add_mcp` for that `(target_root, ide, extension)` pass (i.e. MCP was actually written for that IDE). That automatically includes **all** project-MCP-capable adapters and excludes no-op MCP paths such as Windsurf (`return []`).

Additional trigger: **`add_ide`** — after MCP refresh loops for the **newly added** IDE across all extensions, emit the same notice if **any** `refresh_mcp` in that wave produced non-empty rendered names (prefer **one** emission for the entire `add_ide` invocation, not N copies per extension, if trivial to consolidate).

Multi-extension **`spawn build install`**: emitting once per inner install that merges MCP remains acceptable.

### Message contract

- **Stream:** stdout (distinct from stderr `spawn: warning:` from task 9).

#### Canonical stdout line (exact)

Implementation **must** emit **exactly** this single line followed by **one newline** (equivalent to default `print(...)` in Python: no trailing second newline beyond that).

```
MCP was merged for this workspace; you may need to press Enable in your IDE MCP UI.
```

Constraints: ASCII only; no leading or trailing whitespace on the content line; no `spawn:` prefix; no IDE vendor name.

- **Idempotency:** Not required to dedupe across repeated identical commands beyond what is cheap for `add_ide`.

### Implementation notes

- Implementing emission **inside `refresh_mcp`** (after `save_mcp_rendered`, keyed on non-empty rendered names) minimizes duplicated call sites and naturally covers every IDE registered in Spawn.
- Re-check `IdeCapabilities(..., mcp=...)` only if an adapter contradicts returned names; trust **non-empty `new_names`** as authoritative “MCP was installed for this IDE.”

### Code examples (pseudo)

```python
def refresh_mcp(target_root: Path, ide: str, extension: str) -> None:
    ...
    new_names = adapter.add_mcp(target_root, nm)
    ll.save_mcp_rendered(target_root, ide, extension, new_names)
    if new_names:
        emit_mcp_installed_enable_notice(ide_key=ide)  # or include target path suffix option
```

## Execution Scheme

> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.

- Phase 1 (sequential): step `_DONE_1-core-hint-helper.md` → step `_DONE_2-tests.md`
