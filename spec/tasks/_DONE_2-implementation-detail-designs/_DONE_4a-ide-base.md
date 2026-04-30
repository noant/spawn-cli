# Step 4a: IDE Adapter Base — ABC, Registry, Helpers, Stubs

## Required reading
Before implementing, read:
- `spec/design/ide-adapters.md` — sections: Adapter Registry, Common Adapter Interface, Skill Rendering, MCP Rendering, Entry Point Rendering, Agent Ignore Rendering, Ownership Records, Removal Semantics, Error And Warning Rules

## Goal
Implement the `IdeAdapter` abstract base class, the adapter registry, all shared
rendering helpers (`render_skill_md`, `rewrite_managed_block`, `normalize_skill_name`),
and the `StubAdapter` that backs the 5 warn-only IDEs (qoder, qwen-code, aider, zed, devin).

This step produces the foundation that every concrete IDE adapter (steps 4b–4g) depends on.

## Approach
Create `src/spawn_cli/ide/` as a package. **Canonical IDE key order** is defined
once in `spawn_cli.core.low_level` as `CANONICAL_IDE_KEYS` (no env, no config).
`registry.py` imports that tuple, implements `supported_ide_keys()` as `list(CANONICAL_IDE_KEYS)`,
and iterates **that same order** in `detect_supported_ides`. `register()` must reject
unknown keys. `ide/__init__.py` imports concrete + stub adapters so `_registry`
is populated before first use.

## Affected files

```
src/spawn_cli/ide/__init__.py
src/spawn_cli/ide/registry.py
src/spawn_cli/ide/_stub.py
tests/ide/__init__.py
tests/ide/test_registry.py
```

## `ide/registry.py` — ABC and registry

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from spawn_cli.models.skill import SkillMetadata
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.core.errors import SpawnError
from spawn_cli.core.low_level import CANONICAL_IDE_KEYS

@dataclass
class IdeCapabilities:
    skills: str        # native | project | entry-only | external | unsupported
    mcp: str           # native | project | entry-only | external | unsupported
    agent_ignore: str  # native | project | entry-only | external | unsupported
    entry_point: str   # native | project | entry-only | external | unsupported

    def to_dict(self) -> dict:
        """Serialize to camelCase dict for YAML output."""
        return {
            "skills": self.skills,
            "mcp": self.mcp,
            "agentIgnore": self.agent_ignore,
            "entryPoint": self.entry_point,
        }

@dataclass
class DetectResult:
    used_in_repo: bool
    capabilities: IdeCapabilities

class IdeAdapter(ABC):
    key: str  # canonical key, defined on the class

    @abstractmethod
    def detect(self, target_root: Path) -> DetectResult: ...

    @abstractmethod
    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        """Returns list of {skill: str, path: str} for ownership tracking."""
        ...

    @abstractmethod
    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None: ...

    @abstractmethod
    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        """Returns list of rendered server names."""
        ...

    @abstractmethod
    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None: ...

    @abstractmethod
    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None: ...

    @abstractmethod
    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None: ...

    @abstractmethod
    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        """Returns rendered path or warning string."""
        ...

# Aliases for user-facing command parsing
ALIASES: dict[str, str] = {
    "claude": "claude-code",
    "qwen": "qwen-code",
    "gemini": "gemini-cli",
    "copilot": "github-copilot",
    "github": "github-copilot",
}

_registry: dict[str, IdeAdapter] = {}  # populated at module load by each adapter file

def register(adapter: IdeAdapter) -> None:
    """Register an adapter instance under its canonical key (must appear in CANONICAL_IDE_KEYS)."""
    if adapter.key not in CANONICAL_IDE_KEYS:
        raise SpawnError(f"Cannot register unknown IDE key: {adapter.key!r}")
    _registry[adapter.key] = adapter

def get(name: str) -> IdeAdapter:
    """Resolve alias → canonical key → adapter. SpawnError on unknown."""
    canonical = ALIASES.get(name, name)
    if canonical not in _registry:
        raise SpawnError(f"Unknown IDE: {name!r}")
    return _registry[canonical]

def supported_ide_keys() -> list[str]:
    """Return the frozen ordered list from low_level (not dict iteration order)."""
    return list(CANONICAL_IDE_KEYS)

def detect_supported_ides(target_root: Path) -> dict[str, DetectResult]:
    """Run detect() for every canonical IDE key in CANONICAL_IDE_KEYS order."""
    return {key: get(key).detect(target_root) for key in CANONICAL_IDE_KEYS}
```

## Shared rendering helpers

These helpers live in `registry.py` (or a `_helpers.py` imported by all adapters).

### `normalize_skill_name`

```python
import re

def normalize_skill_name(name: str) -> str:
    """lowercase, trim, replace spaces with '-', keep [a-z0-9._-], collapse repeats."""
    name = name.lower().strip()
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'[^a-z0-9._-]', '', name)
    name = re.sub(r'-{2,}', '-', name)
    return name
```

### `render_skill_md`

Renders normalized skill metadata to Markdown with YAML frontmatter.

```python
def render_skill_md(skill: SkillMetadata) -> str:
    """Render normalized skill to Markdown with frontmatter, nav instruction,
    mandatory reads, contextual reads, and skill body."""
    lines = [
        "---",
        f"name: {skill.name}",
        f"description: {skill.description}",
        "---",
        "",
        "Read `spawn/navigation.yaml` first.",
        "",
    ]
    if skill.required_read:
        lines += ["Mandatory reads:"]
        for ref in skill.required_read:
            lines += [f"- `{ref.file}` - {ref.description}"]
        lines += [""]
    if skill.auto_read:
        lines += ["Contextual reads:"]
        for ref in skill.auto_read:
            lines += [f"- `{ref.file}` - {ref.description}"]
        lines += [""]
    lines += [skill.content]
    return "\n".join(lines)
```

### `rewrite_managed_block`

Entry point managed block — used by all adapters that write to a Markdown entry file.

```python
SPAWN_BLOCK_START = "<!-- spawn:start -->"
SPAWN_BLOCK_END = "<!-- spawn:end -->"

def rewrite_managed_block(file_path: Path, prompt: str) -> None:
    """Read file (or empty string), replace/insert spawn block, write back."""
    import re
    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    block = f"{SPAWN_BLOCK_START}\n{prompt}\n{SPAWN_BLOCK_END}"
    if SPAWN_BLOCK_START in content:
        content = re.sub(
            rf"{re.escape(SPAWN_BLOCK_START)}.*?{re.escape(SPAWN_BLOCK_END)}",
            block, content, flags=re.DOTALL
        )
    else:
        content = block + "\n" + content
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
```

### Agent ignore managed block (text files)

For `.cursorignore`, `.geminiignore`, `.codeiumignore`:

```
# spawn:start
{globs, one per line}
# spawn:end
```

Parsing logic:
- Read existing file (empty string if absent).
- If block found: replace its contents with current Spawn globs.
- If block absent and `add`: append block.
- If block absent and `remove`: no-op.
- Write back.

Implement as `rewrite_ignore_block(file_path: Path, globs: list[str]) -> None` and
`remove_ignore_block(file_path: Path, globs: list[str]) -> None`.

## `_stub.py` — warn-only adapter for qoder, qwen-code, aider, zed, devin

```python
import warnings
from pathlib import Path
from spawn_cli.ide.registry import IdeAdapter, IdeCapabilities, DetectResult, register
from spawn_cli.models.skill import SkillMetadata
from spawn_cli.models.mcp import NormalizedMcp

class StubAdapter(IdeAdapter):
    def __init__(self, key: str, caps: IdeCapabilities) -> None:
        self.key = key
        self._caps = caps

    def detect(self, target_root: Path) -> DetectResult:
        return DetectResult(used_in_repo=False, capabilities=self._caps)

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        warnings.warn(f"{self.key}: skill rendering not yet implemented")
        return []

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        warnings.warn(f"{self.key}: skill removal not yet implemented")

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        warnings.warn(f"{self.key}: MCP rendering not yet implemented")
        return []

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        warnings.warn(f"{self.key}: MCP removal not yet implemented")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        warnings.warn(f"{self.key}: agent ignore not yet implemented")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        warnings.warn(f"{self.key}: agent ignore removal not yet implemented")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        warnings.warn(f"{self.key}: entry point not yet implemented")
        return ""

# Register warn-only stubs
_STUBS = [
    ("qoder",     IdeCapabilities("native", "project", "project", "agents-md")),
    ("qwen-code", IdeCapabilities("native", "project", "project", "qwen-md")),
    ("aider",     IdeCapabilities("entry-only", "unsupported", "project", "conventions-md")),
    ("zed",       IdeCapabilities("unsupported", "project", "unsupported", "agents-md")),
    ("devin",     IdeCapabilities("native", "project", "unsupported", "agents-md")),
]

for _key, _caps in _STUBS:
    register(StubAdapter(_key, _caps))
```

## `ide/__init__.py`

Import all adapter modules to trigger side-effect registrations:

```python
from spawn_cli.ide import registry  # noqa: F401
from spawn_cli.ide import _stub     # noqa: F401
# concrete adapters imported once they exist:
# from spawn_cli.ide import cursor, codex, claude_code, github_copilot, gemini_cli, windsurf
```

After each adapter step (4b–4g) is implemented, its import line is uncommented here.

## Tests — `tests/ide/test_registry.py`

- `test_get_known_adapter` — after all adapters registered: cursor, codex, etc. return correct instance
- `test_get_alias` — `"claude"` → `ClaudeCodeAdapter`; `"gemini"` → `GeminiCliAdapter`
- `test_get_unknown_raises` — unknown name → `SpawnError`
- `test_detect_supported_ides` — returns `DetectResult` for all 11 IDEs (stubs included)
- `test_normalize_skill_name` — spaces→dashes, uppercase→lowercase, invalid chars stripped, double-dash collapsed
- `test_render_skill_md_minimal` — no required_read, no auto_read → correct frontmatter + nav line
- `test_render_skill_md_full` — required_read + auto_read sections rendered in correct order
- `test_rewrite_managed_block_creates` — file absent → block prepended to empty content
- `test_rewrite_managed_block_replaces` — existing block → replaced, surrounding content preserved
- `test_rewrite_ignore_block_add` — no block → block appended
- `test_rewrite_ignore_block_replace` — existing block → globs replaced
- `test_remove_ignore_block` — block present → removed, surrounding lines preserved

## Sequencing note

Steps 4b–4g each call `register(...)` at module load time. This step (4a) must be
merged first so the registry infrastructure is in place before any adapter is committed.
