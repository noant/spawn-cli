# New IDE Adapter Checklist

Adding an IDE adapter touches a fixed set of places. Land them together (one task) so the package never imports a missing module.

## Checklist (in order)

1. Append the canonical key to `CANONICAL_IDE_KEYS` in `src/spawn_cli/core/low_level.py` (append-only; `registry.register()` raises `SpawnError` otherwise).
2. Create `src/spawn_cli/ide/{ide}.py`: class `{Ide}Adapter(IdeAdapter)`, module-level `register({Ide}Adapter())`, `__all__`.
3. Wire `src/spawn_cli/ide/__init__.py`: `from . import {ide}  # noqa: F401`, class re-export, `__all__` entry.
4. Optional alias in `ALIASES` (`src/spawn_cli/ide/registry.py`) for short CLI names.
5. Vacancy pruner: `finalize_{ide}_repo` in `src/spawn_cli/ide/_vacancy.py` covering every config subtree the adapter writes (rule 01); add to `__all__`.
6. Pick the closest config-family precedent and copy its mechanics:
   - JSON config with `mcp` key + `permission` deny globs: `opencode.py` (also Mimo Code — OpenCode fork).
   - TOML config: `codex.py`; text ignore files: `cursor.py` / `cline.py`.
7. Canonical config file rules (rule 05): one canonical file; SpawnWarning when only a JSONC/variant exists; SpawnError on unparseable canonical file before mutation.
8. Warnings/errors via `SpawnWarning`/`SpawnError` from `spawn_cli.errors` (rule 03).
9. Tests mirroring the precedent adapter (`tests/ide/test_{ide}.py`), plus:
   - `tests/ide/test_registry.py`: key + alias assertions.
   - `tests/ide/test_mcp_stdio_proxy_parity.py`: add the adapter to the parametrize list.
10. Update docs: `spec/design/ide-adapters.md` (canonical keys, aliases, IDE Matrix, entry-point and agent-ignore tables) and the adapter list in `spec/design/hla.md`.

## Capability pitfalls (from task 30, Hermes)

- Use `skills="native"` for dot-dir skills — never `"project"` (no peer uses that value).
- Global-profile tools (MCP/ignore live only in home-dir config): set `mcp`/`agent_ignore` to `"unsupported"` + `SpawnWarning` (mirror `cline.py`); do NOT invent a project config file the tool ignores. Skip the parity-test param when MCP is unsupported.
- Pick a specific `entry_point` tag matching the file actually written (`"hermes-md"`, `"agents-md"`, `"claude-md"`, ...) and prefer the tool's native highest-priority context file over shared `AGENTS.md` when upstream shadowing applies (Hermes: `.hermes.md` > `AGENTS.md`).
- No ALIASES entry for single-token keys; aliases are for multi-word names only.
- Vacancy pruner prunes only when the dotdir is EMPTY (`dir_has_any_file` guard) — vacancy tests must create empty dirs, not files.

## Detect marker rule

Never use `AGENTS.md` (or other shared rule files) as the sole detect marker — it is shared across agents. Use the IDE's own dotdir or config file.

## Example

```python
class MimoCodeAdapter(IdeAdapter):
    key = "mimo-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".mimocode").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(skills="native", mcp="project", agent_ignore="project", entry_point="agents-md"),
        )


register(MimoCodeAdapter())
```
