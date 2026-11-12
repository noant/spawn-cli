# Step 2: finalize_codex_repo permissions-aware cleanup

Status: Done
Suggested model: GLM-5.3-flash
Used model: GLM-5.3-flash

## Goal
Make `finalize_codex_repo` remove the spawn permissions subtree and delete `config.toml` when only empty `mcp_servers`/`permissions` remain.

## Approach
- Extend the existing vacancy condition; keep behavior identical for legacy configs (only `mcp_servers`).
- Remove the spawn-namespaced profile before evaluating emptiness; never touch foreign permission profiles.

## Affected files
- `src/spawn_cli/ide/_vacancy.py` — `finalize_codex_repo` (L176-196).

## Code changes (before / after)

### `src/spawn_cli/ide/_vacancy.py` — `finalize_codex_repo` config cleanup

**Before**
```python
    if codex_cfg.is_file():
        data = load_toml(codex_cfg)
        if isinstance(data, dict) and (
            data == {} or (set(data.keys()) <= {"mcp_servers"} and not data.get("mcp_servers"))
        ):
            codex_cfg.unlink(missing_ok=True)
```
Deletes config.toml only when it is empty or contains an empty `mcp_servers` table; a leftover `[permissions.spawn]` (possibly empty after `clear_spawn_agent_ignore`) keeps the file alive forever.

**After**
```python
    if codex_cfg.is_file():
        data = load_toml(codex_cfg)
        if isinstance(data, dict):
            permissions = data.get("permissions")
            if isinstance(permissions, dict):
                profile = permissions.get("spawn")
                if isinstance(profile, dict):
                    fs = profile.get("filesystem")
                    fs = fs if isinstance(fs, dict) else {}
                    if not fs.get(":workspace_roots"):
                        permissions.pop("spawn", None)
                if not permissions:
                    data.pop("permissions", None)
        if isinstance(data, dict) and (
            data == {}
            or (
                set(data.keys()) <= {"mcp_servers", "permissions"}
                and not data.get("mcp_servers")
                and not data.get("permissions")
            )
        ):
            codex_cfg.unlink(missing_ok=True)
```
Drops the spawn profile when it has no deny rules left (foreign/user deny rules under `permissions.spawn` are preserved by removal via the adapter, not here; non-dict `filesystem` is treated as empty), then applies the extended vacancy condition; configs containing only empty `mcp_servers`/`permissions` are deleted as before.

Note: use the literal `"spawn"` here or import `SPAWN_PERMISSIONS_PROFILE` from `spawn_cli.ide.codex` — importing is preferred to avoid drift, but `_vacancy` must not import the adapter module at module import time; use a local import inside the function (`from spawn_cli.ide.codex import SPAWN_PERMISSIONS_PROFILE`) mirroring the existing local `load_toml` import pattern.

## Additional actions
- Verification: `pytest tests/ide/test_vacancy.py -k codex` — the file is created by Step 3 (verified: it does not exist today); until then this command errors, which is expected inside Step 5 sequencing.
