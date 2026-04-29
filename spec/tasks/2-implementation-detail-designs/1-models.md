# Step 1: Pydantic Data Models and I/O Helpers

## Required reading
Before implementing, read:
- `spec/design/data-structure.md` — all config, metadata, navigation, MCP, and skill shapes that must become models

## Goal
Define all typed data models and file I/O utilities that the rest of the codebase depends on.

## Approach
Create `src/spawn_cli/models/` and `src/spawn_cli/io/` subpackages. Every shape defined in the design documents becomes a Pydantic v2 model. I/O helpers wrap ruamel.yaml, json, tomllib, and text reads/writes with consistent error handling.

## Affected files

```
src/spawn_cli/models/__init__.py
src/spawn_cli/models/config.py
src/spawn_cli/models/metadata.py
src/spawn_cli/models/navigation.py
src/spawn_cli/models/mcp.py
src/spawn_cli/models/skill.py

src/spawn_cli/io/__init__.py
src/spawn_cli/io/yaml_io.py
src/spawn_cli/io/json_io.py
src/spawn_cli/io/toml_io.py
src/spawn_cli/io/text_io.py
src/spawn_cli/io/paths.py
src/spawn_cli/io/lock.py

pyproject.toml  (add deps: pydantic, ruamel.yaml, filelock, httpx, tomli/tomllib)
```

## Models

### `models/config.py`
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class FileMode(str, Enum):
    static = "static"
    artifact = "artifact"

class ReadFlag(str, Enum):
    required = "required"
    auto = "auto"
    no = "no"

class ExtensionFileEntry(BaseModel):
    description: Optional[str] = None
    mode: FileMode = FileMode.static
    globalRead: ReadFlag = ReadFlag.no
    localRead: ReadFlag = ReadFlag.no

class ExtensionFolderEntry(BaseModel):
    mode: FileMode = FileMode.static

class SkillEntry(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    required_read: list[str] = Field(default_factory=list, alias="required-read")

class SetupConfig(BaseModel):
    before_install: Optional[str] = Field(None, alias="before-install")
    after_install: Optional[str] = Field(None, alias="after-install")
    before_uninstall: Optional[str] = Field(None, alias="before-uninstall")
    after_uninstall: Optional[str] = Field(None, alias="after-uninstall")
    healthcheck: Optional[str] = None

class ExtensionConfig(BaseModel):
    name: Optional[str] = None
    version: str
    schema_version: int = Field(1, alias="schema")
    files: dict[str, ExtensionFileEntry] = Field(default_factory=dict)
    folders: dict[str, ExtensionFolderEntry] = Field(default_factory=dict)
    agent_ignore: list[str] = Field(default_factory=list, alias="agent-ignore")
    git_ignore: list[str] = Field(default_factory=list, alias="git-ignore")
    skills: dict[str, SkillEntry] = Field(default_factory=dict)
    setup: Optional[SetupConfig] = None

class CoreConfig(BaseModel):
    version: str
    agent_ignore: list[str] = Field(default_factory=list, alias="agent-ignore")

class IdeList(BaseModel):
    ides: list[str] = Field(default_factory=list)

class SourceYaml(BaseModel):
    class SourceInfo(BaseModel):
        type: str  # git | zip | local
        path: str
        branch: Optional[str] = None
        resolved: Optional[str] = None

    class InstalledInfo(BaseModel):
        version: str
        installedAt: str

    extension: str
    source: SourceInfo
    installed: InstalledInfo

class ExtensionsMeta(BaseModel):
    class ExtEntry(BaseModel):
        path: str
        branch: Optional[str] = None
    extensions: list[ExtEntry] = Field(default_factory=list)
```

### `models/metadata.py`
```python
class RenderedSkillEntry(BaseModel):
    skill: str   # source skill filename
    path: str    # rendered path in target repo

class RenderedSkillsMeta(BaseModel):
    extensions: dict[str, list[RenderedSkillEntry]] = Field(default_factory=dict)

class RenderedMcpEntry(BaseModel):
    name: str

class RenderedMcpMeta(BaseModel):
    extensions: dict[str, list[RenderedMcpEntry]] = Field(default_factory=dict)
```

### `models/navigation.py`
```python
class NavFile(BaseModel):
    path: str
    description: str

class NavExtGroup(BaseModel):
    ext: str
    files: list[NavFile] = Field(default_factory=list)

class NavRulesGroup(BaseModel):
    rules: list[NavFile] = Field(default_factory=list)

# read-required and read-contextual items are either NavExtGroup or NavRulesGroup
class NavigationFile(BaseModel):
    read_required: list[dict] = Field(default_factory=list, alias="read-required")
    read_contextual: list[dict] = Field(default_factory=list, alias="read-contextual")
```

### `models/mcp.py`
```python
class McpEnvVar(BaseModel):
    source: str = "user"
    required: bool = True
    secret: bool = False

class McpCapabilities(BaseModel):
    tools: bool = True
    resources: bool = False
    prompts: bool = False

class McpTransport(BaseModel):
    type: str  # stdio | http | sse
    command: Optional[str] = None
    args: list[str] = Field(default_factory=list)
    cwd: str = "."
    url: Optional[str] = None

class McpServer(BaseModel):
    name: str
    extension: str
    transport: McpTransport
    env: dict[str, McpEnvVar] = Field(default_factory=dict)
    capabilities: McpCapabilities = Field(default_factory=McpCapabilities)

class NormalizedMcp(BaseModel):
    servers: list[McpServer] = Field(default_factory=list)
```

### `models/skill.py`
```python
class SkillFileRef(BaseModel):
    file: str
    description: str

class SkillRawInfo(BaseModel):
    name: str
    description: str
    content: str              # body without frontmatter
    required_read: list[str] = Field(default_factory=list, alias="required-read")

class SkillMetadata(BaseModel):
    name: str
    description: str
    content: str
    required_read: list[SkillFileRef] = Field(default_factory=list)
    auto_read: list[SkillFileRef] = Field(default_factory=list)
```

## I/O Helpers

### `io/yaml_io.py`
- `load_yaml(path: Path) -> dict` — ruamel.yaml load; returns `{}` if missing
- `save_yaml(path: Path, data: dict) -> None` — ruamel.yaml dump, `ensure_dir` first

### `io/json_io.py`
- `load_json(path: Path) -> dict` — json.loads; returns `{}` if missing
- `save_json(path: Path, data: dict, indent: int = 2) -> None`

### `io/toml_io.py`
- `load_toml(path: Path) -> dict` — tomllib.loads (Python 3.11+) or tomli fallback; returns `{}` if missing
- `save_toml(path: Path, data: dict) -> None` — tomli-w

### `io/text_io.py`
- `read_lines(path: Path) -> list[str]` — returns `[]` if missing
- `write_lines(path: Path, lines: list[str]) -> None`

### `io/paths.py`
- `ensure_dir(path: Path) -> None`
- `safe_path(root: Path, rel: str) -> Path` — raises SpawnError if rel escapes root
- `spawn_root(target: Path) -> Path` — returns `target / "spawn"`

### `io/lock.py`
```python
from filelock import FileLock
from contextlib import contextmanager

@contextmanager
def spawn_lock(target_root: Path):
    lock_path = target_root / "spawn" / ".metadata" / ".spawn.lock"
    ensure_dir(lock_path.parent)
    with FileLock(str(lock_path)):
        yield
```

## Code examples

```python
# Using the lock:
with spawn_lock(target_root):
    init(target_root)

# Loading extension config:
raw = load_yaml(target_root / "spawn" / ".extend" / ext / "config.yaml")
config = ExtensionConfig.model_validate(raw)
```

## Dependencies to add in `pyproject.toml`
- `pydantic>=2.0`
- `ruamel.yaml>=0.18`
- `filelock>=3.12`
- `httpx>=0.27`
- `tomli>=2.0; python_version < "3.11"` (or use `tomllib` stdlib for 3.11+)
- `tomli-w>=1.0`

## Tests to write
- `tests/models/test_config.py` — parse valid/invalid ExtensionConfig, check enum validation, alias handling
- `tests/models/test_metadata.py` — parse RenderedSkillsMeta, RenderedMcpMeta
- `tests/models/test_navigation.py` — parse NavigationFile
- `tests/models/test_mcp.py` — parse NormalizedMcp shapes
- `tests/models/test_skill.py` — parse SkillMetadata
- `tests/io/test_yaml_io.py` — load/save roundtrip, missing file returns `{}`
- `tests/io/test_json_io.py` — load/save roundtrip
- `tests/io/test_toml_io.py` — load/save roundtrip
- `tests/io/test_text_io.py` — read/write lines
- `tests/io/test_paths.py` — safe_path escape detection
- `tests/io/test_lock.py` — lock acquires and releases cleanly
