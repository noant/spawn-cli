# Rule: vacancy-cleanup knows every adapter-written config subtree

Required. Applies to any IDE adapter that writes into a project config file.

When an adapter adds a new top-level key or subtree to a shared config file
(e.g. `.codex/config.toml`, `.claude/settings.json`), the matching
`finalize_*_repo` cleanup MUST be extended in the same task to know that key.
Otherwise `spawn ide remove <ide>` leaves a "dead" config file (or `.dir/`)
forever, because the vacancy condition only recognizes the keys it knows.

Contract:

1. The finalize function must be able to recognize every subtree the adapter
   can write, including spawn-namespaced ones.
2. The finalize function may prune only spawn-owned subtrees (empty after
   glob/entry removal); user-owned entries in the same file are preserved.
3. The deletion condition is: file is empty, or contains only known keys and
   all of them are empty.

Example (from task 26, `finalize_codex_repo`): before the fix, the condition
only knew `mcp_servers`, so an empty `[permissions.spawn]` kept the file alive:

```python
if isinstance(data, dict) and (
    data == {} or (set(data.keys()) <= {"mcp_servers"} and not data.get("mcp_servers"))
):
    codex_cfg.unlink(missing_ok=True)
```

After — drop the spawn-owned subtree, then extend the known-key set:

```python
permissions = data.get("permissions")
if isinstance(permissions, dict):
    profile = permissions.get(SPAWN_PERMISSIONS_PROFILE)
    if isinstance(profile, dict) and not profile.get("filesystem", {}).get(":workspace_roots"):
        permissions.pop(SPAWN_PERMISSIONS_PROFILE, None)
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

Checklist for any new adapter-written config key:

- [ ] update `finalize_*_repo` condition (this rule)
- [ ] add a cleanup test (file deleted when only empty known keys remain;
      file kept when user content remains)
