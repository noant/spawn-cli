# Adapter warnings use SpawnWarning

IDE adapters must emit user-facing warnings with the `SpawnWarning` category
(`spawn_cli.errors.SpawnWarning`), not plain `UserWarning`:

```python
from spawn_cli.errors import SpawnWarning
warnings.warn("Cline has no project-scope MCP settings; ...", SpawnWarning)
```

The CLI installs `install_spawn_warning_format` (task 9), which prints
`SpawnWarning` as a single friendly line `spawn: warning: <text>`; plain
`UserWarning` renders as a Python traceback with file/line noise.
