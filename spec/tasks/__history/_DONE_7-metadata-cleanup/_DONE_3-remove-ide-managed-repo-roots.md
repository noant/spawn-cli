# 3-remove-ide-managed-repo-roots

## Goal

After Spawn tears down an IDE integration (`spawn ide remove <ide>`), **detect** when the IDE-managed root directory (for example `.cursor`) contains no meaningful user data and the MCP config file is reduced to an **empty** MCP payload, then **unlink the MCP file when empty** and **delete the entire IDE root directory**.

Do **not** delete user-owned content or shared tooling directories wholesale (see vacancy rules below).

## Vacancy detection (required behaviour)

Implement shared or per-adapter helpers with **deterministic predicates**:

1. **`mcp_json_is_empty(path: Path) -> bool`** — apply **only when `path.is_file()`**; if the file does not exist, skip (predicate not used).

   Parse JSON on success; **empty for removal** when MCP server payloads are depleted:
     - **Cursor-style** (`.cursor/mcp.json`, VS Code-style `mcpServers`): `mcpServers` is absent, `null`, or `{}`. If the document is literally `{}`, treat as empty. If other top-level keys exist with **non-empty** values, treat as **not empty** (preserve file) unless a future task adds ownership metadata for those keys.
   - Same predicate pattern for other adapters that merge into project-root `.mcp.json`: empty only when the merged structure has no non-empty server map **and** no other non-empty Spawn-irrelevant keys the implementation cannot classify as user data (conservative default: if any unknown non-empty key remains, do not delete file).

2. **`ide_root_dir_is_removable(root: Path, *, allow_delete_entire: bool) -> bool`**:

   - **`root`** is the adapter-specific IDE directory (e.g. `target_root / ".cursor"`).
   - **`allow_delete_entire`**: `True` only for roots that are IDE-dedicated (Cursor, Gemini, Windsurf, Claude `.claude`, Codex split paths per adapter); `False` for `.github` / `.vscode`.
   - Directory is **removable** when:
     - `root` exists and `allow_delete_entire` is `True`, **and**
     - after unlinking an empty MCP JSON at `root / "mcp.json"` (or adapter path) if applicable, **every** remaining descendant is either gone or only empty directories, **or** only contains files/dirs that Spawn’s own install layout could have created **and** none have non-empty user content.
   - Practical rule for **Cursor**: recurse; if any file exists with non-zero size or any directory contains any file, **`root` is not removable**. After removing `mcp.json` when `mcp_json_is_empty`, if `root` has **no entries** (or only empty dirs cleaned bottoms-up), **`rmtree(root, ignore_errors=True)`** or equivalent.

3. **Order of operations per adapter** (example Cursor):

   - Run existing per-file removals from `remove_*` (already done before this hook).
   - If `mcp.json` exists and `mcp_json_is_empty`, **unlink** it.
   - Prune empty directories bottoms-up under `root` (e.g. vacant `skills/`).
   - If `ide_root_dir_is_removable(root, allow_delete_entire=True)`, **delete `root` entirely**.

4. **Equivalence for "other" IDE folders** — apply the same logical pattern: **unlink empty MCP artifact first**, then remove **entire** `.gemini`, `.windsurf`, `.claude`, etc., when the vacancy predicate passes; for **split** layouts (Codex: `.codex` vs `.agents`), each top-level directory Spawn treats as an IDE root must individually pass the same checks.

## Approach

1. Extend `IdeAdapter` with a concrete (non-abstract) hook with default empty body:

   `finalize_repo_after_ide_removed(self, target_root: Path) -> None`

   Spawn calls `ide_get(ide).finalize_repo_after_ide_removed(target_root)` exactly once inside `high_level.remove_ide`, **after** all per-extension `remove_mcp` / `remove_skills` and IDE `remove_agent_ignore` paths have finished, **before** `remove_ide_from_list` and before `spawn/.metadata/<ide>/` is removed.

2. **Cursor** (`cursor`): Apply **Vacancy detection** to `target_root / ".cursor"` with `allow_delete_entire=True`.

   Implementation must **explicitly** implement `mcp_json_is_empty` for `.cursor/mcp.json` and **remove the whole `.cursor` directory** when removable per `ide_root_dir_is_removable`.

   Caveat (unchanged): entries in `mcpServers` not created by Spawn cannot be distinguished; empty `{}` still means the file is redundant and the folder may be removed if nothing else remains.

3. **Other adapters** — same hook, same **Vacancy detection** pattern; **github-copilot**: `allow_delete_entire=False` for `.github` and `.vscode`; only unlink empty `mcp.json` under `.vscode` and remove vacant `.github/skills` subtree, **never** `rmtree(".github")` or `.vscode` as a whole unless a future spec narrows a dedicated subfolder that is provably Spawn-only and empty.

4. **Stub** adapters: keep default no-op unless they acquire root-managed trees.


## Affected files

- `src/spawn_cli/ide/registry.py` — `IdeAdapter` method + docs.
- `src/spawn_cli/ide/*.py` — per-adapter overrides.
- `src/spawn_cli/core/high_level.py` — invoke hook in `remove_ide`.
- `tests/` — Cursor-focused test asserting `.cursor` absent when only Spawn-created layout existed; optionally one negative test with a dummy extra file under `.cursor/rules` asserting `.cursor` remains.

## Code sketch

```python
def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
    return  # default

# CursorAdapter:
def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
    root = target_root / ".cursor"
    mcp = root / "mcp.json"
    if mcp_json_is_empty(mcp):  # implements predicate above
        mcp.unlink(missing_ok=True)
    prune_empty_parents_under_cursor(root)
    if ide_root_dir_is_removable(root, allow_delete_entire=True):
        shutil.rmtree(root, ignore_errors=True)
```
