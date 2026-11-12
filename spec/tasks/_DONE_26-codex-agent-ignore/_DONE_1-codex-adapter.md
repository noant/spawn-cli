# Step 1: CodexAdapter agent-ignore via permissions profile

Status: Done
Suggested model: GLM-5.3-flash
Used model: GLM-5.3-flash

## Goal
Implement deny-rule based agent ignore in `CodexAdapter` and switch capability to `project`.

## Approach
- Mirror the Claude Code pattern (`src/spawn_cli/ide/claude_code.py` L103-137), adapted to TOML.
- Write only into the spawn-namespaced profile; never write `default_permissions`.
- Idempotency: deny entries live in a dict keyed by glob, so re-adding is a no-op.
- Warn when the project config already sets top-level `sandbox_mode` (deny rules inert due to mutual exclusion).

## Affected files
- `src/spawn_cli/ide/codex.py` — `CodexAdapter.detect`, `add_agent_ignore`, `remove_agent_ignore`, new `clear_spawn_agent_ignore`, new module constant `SPAWN_PERMISSIONS_PROFILE`.

## Code changes (before / after)

### `src/spawn_cli/ide/codex.py` — `CodexAdapter.detect` capability value

**Before**
```python
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="unsupported",
                entry_point="agents-md",
            ),
```
Declares codex as not supporting agent ignore; high-level flows skip ignore sync.

**After**
```python
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="project",
                entry_point="agents-md",
            ),
```
Declares project-config based ignore; `_sync_project_agent_ignore_permissions` now runs for codex.

### `src/spawn_cli/ide/codex.py` — module constant (new, after imports)

**Before**
(insertion context: after the import block ending with `from spawn_cli.models.skill import SkillMetadata`, before `def _build_toml_server_entry`)
(no existing code)

**After**
```python
SPAWN_PERMISSIONS_PROFILE = "spawn"
```
Namespace key for the spawn-managed permission profile in `.codex/config.toml`.

### `src/spawn_cli/ide/codex.py` — `CodexAdapter.add_agent_ignore` / `remove_agent_ignore`

**Before**
```python
    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("codex: agent ignore is unsupported; steer via AGENTS.md policy instead")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("codex: agent ignore is unsupported")
```
Warn stubs; spawn ignore globs are never applied for codex.

**After**
```python
    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        config_path = target_root / ".codex" / "config.toml"
        data = load_toml(config_path)
        if "sandbox_mode" in data:
            warnings.warn(
                "codex: sandbox_mode is set; permissions.spawn deny rules are inert "
                "unless the user switches to default_permissions"
            )
        profile = data.setdefault("permissions", {}).setdefault(SPAWN_PERMISSIONS_PROFILE, {})
        if "extends" not in profile:
            profile["extends"] = ":workspace"
        filesystem = profile.setdefault("filesystem", {})
        if not isinstance(filesystem, dict):
            filesystem = {}
            profile["filesystem"] = filesystem
        fs_rules = filesystem.setdefault(":workspace_roots", {})
        if not isinstance(fs_rules, dict):
            fs_rules = {}
            filesystem[":workspace_roots"] = fs_rules
        for glob in globs:
            fs_rules[glob] = "deny"
        save_toml(config_path, data)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        config_path = target_root / ".codex" / "config.toml"
        if not config_path.is_file():
            return
        data = load_toml(config_path)
        permissions = data.get("permissions")
        if not isinstance(permissions, dict):
            return
        profile = permissions.get(SPAWN_PERMISSIONS_PROFILE)
        if not isinstance(profile, dict):
            return
        fs_rules = profile.get("filesystem")
        if not isinstance(fs_rules, dict):
            fs_rules = {}
            profile["filesystem"] = fs_rules
        rules = fs_rules.get(":workspace_roots")
        if isinstance(rules, dict):
            drop = set(globs)
            for glob in drop:
                rules.pop(glob, None)
            if not rules:
                fs_rules.pop(":workspace_roots", None)
                if not fs_rules:
                    profile.pop("filesystem", None)
        if not profile or set(profile) <= {"extends"}:
            permissions.pop(SPAWN_PERMISSIONS_PROFILE, None)
            if not permissions:
                data.pop("permissions", None)
        save_toml(config_path, data)
```
Adds/removes `"glob" = "deny"` entries under `[permissions.spawn.filesystem.":workspace_roots"]`; prunes empty nested tables so the config never keeps vacant spawn subtrees (a profile reduced to only the spawn-written boilerplate `extends` is also dropped); coerces non-dict `filesystem`/`":workspace_roots"` values (same guard pattern as `add_mcp`); re-adding an existing glob is a no-op (dict key).

### `src/spawn_cli/ide/codex.py` — new `clear_spawn_agent_ignore` (insert after `remove_agent_ignore`)

**Before**
(insertion context: between the new `remove_agent_ignore` and `def rewrite_entry_point`; the base class hook from `registry.py` L87-88 is a no-op `del target_root`)

**After**
```python
    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        recorded = ll.get_agent_ignore_list(target_root, self.key)
        if recorded:
            self.remove_agent_ignore(target_root, recorded)
```
Full rollback on `spawn ide remove codex`, mirroring `claude_code.py` L134-137; requires import `from spawn_cli.core import low_level as ll` (no circular-import risk: `core.low_level` does not import `spawn_cli.ide`).

## Additional actions
- After implementation, run the test suite subset: `pytest tests/ide/test_codex.py` (until Step 3, three tests will fail: `test_detect_with_codex_dir` expects the old capability, `test_add_agent_ignore_warns`/`test_remove_agent_ignore_warns` expect warn stubs — acceptable only inside Step 5 sequencing, Step 1 coder may leave them failing, Step 3 fixes them).
