# Step 1: Core orchestration

## Goal
Centralize “refresh rendered skills for every installed extension” and invoke it from all extension-set mutation paths that currently leave peer skills stale.

## Approach
1. Introduce a small helper on `high_level` (private) that, for a given `target_root` and `ide`, calls `refresh_skills(target_root, ide, ext)` for each `ext` in `ll.list_extensions(target_root)` in stable order.
2. **`_refresh_extension_core(target_root, extension)`**  
   - Per IDE: call `refresh_mcp` only for the `extension` argument (preserve existing MCP merge notice behavior).  
   - Per IDE: call the new helper to refresh skills for **all** extensions (including the one just installed/updated).
3. **`remove_extension`**: After removing the extension’s rendered IDE assets and deleting `spawn/.extend/{ext}`, `refresh_gitignore`, `refresh_navigation`, and per-IDE `refresh_agent_ignore` / `refresh_entry_point`, invoke the same per-IDE “refresh all skills” helper for **remaining** extensions (iterate `ll.list_extensions`—the removed name is already absent).
4. **`refresh_extension_for_ide`**: Update so `refresh_skills` runs for all installed extensions on that IDE; keep `refresh_mcp` scoped to the passed `extension` only. Extend the docstring to state why all skills are touched.

## Affected files
- `src/spawn_cli/core/high_level.py`

## Notes
- Do not change `low_level.generate_skills_metadata` merge rules in this step.
- If `list_extensions` order is not guaranteed stable, wrap with `sorted(...)` for reproducible adapter writes and tests.
