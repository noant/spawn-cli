# Step 1: Registration wiring

Status: Done
Suggested model: glm-5.3-flash
Used model: GLM-5.3-flash

## Goal
Register the `mimo-code` canonical IDE key and wire the adapter module into the IDE package so `register()` accepts the new adapter.

## Approach
Append-only change to `CANONICAL_IDE_KEYS` (ordering preserved); mirror the opencode wiring lines in `ide/__init__.py`; add the `mimo` alias.

## Affected files
- `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS`
- `src/spawn_cli/ide/__init__.py` — module import, re-export, `__all__`
- `src/spawn_cli/ide/registry.py` — `ALIASES`

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` (module constant, line 28-37)

**Before**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
    "cline",
    "opencode",
)
```
The canonical list of IDE keys; `registry.register()` rejects any key not in it (`SpawnError("Cannot register unknown IDE key")`), so `mimo-code` cannot be registered today.

**After**
```python
CANONICAL_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "codex",
    "claude-code",
    "windsurf",
    "github-copilot",
    "gemini-cli",
    "cline",
    "opencode",
    "mimo-code",
)
```
Appends `mimo-code` as the ninth canonical key; registry accepts the Mimo adapter; `detect_supported_ides` picks it up automatically.

### `src/spawn_cli/ide/__init__.py` — module imports (top import block, line 12)

**Before**
```python
from . import opencode  # noqa: F401
```
Side-effect import chain that registers all concrete adapters at package import.

**After**
```python
from . import opencode  # noqa: F401
from . import mimo_code  # noqa: F401
```
Imports the new adapter module so `register(MimoCodeAdapter())` runs at package import.

### `src/spawn_cli/ide/__init__.py` — class re-export (line 15) and `__all__` (line 47)

**Before**
```python
from .opencode import OpenCodeAdapter
```
```python
__all__ = [
    "ALIASES",
    "ClineAdapter",
    "OpenCodeAdapter",
```
Re-exports concrete adapter classes for `spawn_cli.ide` consumers; `MimoCodeAdapter` is missing.

**After**
```python
from .opencode import OpenCodeAdapter
from .mimo_code import MimoCodeAdapter
```
```python
__all__ = [
    "ALIASES",
    "ClineAdapter",
    "OpenCodeAdapter",
    "MimoCodeAdapter",
```
Exposes `MimoCodeAdapter` on the package.

### `src/spawn_cli/ide/registry.py` — `ALIASES` (dict, ~line 100-105)

**Before**
```python
ALIASES: dict[str, str] = {
    "claude": "claude-code",
    "gemini": "gemini-cli",
    "copilot": "github-copilot",
    "github": "github-copilot",
}
```
Short-name aliases resolved by `registry.get()`; no alias for Mimo.

**After**
```python
ALIASES: dict[str, str] = {
    "claude": "claude-code",
    "gemini": "gemini-cli",
    "copilot": "github-copilot",
    "github": "github-copilot",
    "mimo": "mimo-code",
}
```
`spawn ... mimo` resolves to the `mimo-code` adapter.

## Additional actions
None — the adapter module itself is created in step 2; this step only prepares the wiring (imports of a not-yet-existing module will fail until step 2 lands; steps are sequential).
