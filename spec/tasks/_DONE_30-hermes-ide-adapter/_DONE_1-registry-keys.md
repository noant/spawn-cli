# Step 1: Register "hermes" canonical key

Status: Done
Suggested model: glm-5.3-flash
Used model: glm-5.3-flash

## Goal
Add `"hermes"` to `CANONICAL_IDE_KEYS` and wire the (new) adapter module import/export so `get("hermes")` resolves after Step 2.

## Approach
Append-only ordering convention (reviewer-confirmed). No ALIASES entry needed (single-token key). Registration validation in `register()` (registry.py:110) requires key membership before `HermesAdapter` registration in Step 2 works.

## Affected files
- `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` tuple
- `src/spawn_cli/ide/__init__.py` — module import + class export + `__all__`

## Code changes (before / after)

### `src/spawn_cli/core/low_level.py` — CANONICAL_IDE_KEYS

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
Canonical, frozen-order list of supported IDE keys; drives `detect_supported_ides()` ordering and `register()` validation.

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
    "hermes",
)
```
"hermes" appended last (append-only convention); detect ordering now includes hermes.

### `src/spawn_cli/ide/__init__.py` — import + export

**Before**
```python
from . import cline  # noqa: F401
from . import opencode  # noqa: F401
```
Side-effect imports registering adapters.

**After**
```python
from . import cline  # noqa: F401
from . import opencode  # noqa: F401
from . import hermes  # noqa: F401
```
Adds hermes module import (its bottom `register(HermesAdapter())` runs at load; module created in Step 2).

### `src/spawn_cli/ide/__init__.py` — class export

**Before**
```python
from .opencode import OpenCodeAdapter
```
Concrete adapter class re-export.

**After**
```python
from .opencode import OpenCodeAdapter
from .hermes import HermesAdapter
```
Exposes HermesAdapter to package consumers.

Also add `"HermesAdapter"` to `__all__` next to `"OpenCodeAdapter"`.

## Additional actions
- None. Module `src/spawn_cli/ide/hermes.py` does not exist yet; to keep this step importable alone, it is acceptable to merge Steps 1 and 2 in one commit sequence (Step 2 immediately after). Do NOT run the package import check standalone.
