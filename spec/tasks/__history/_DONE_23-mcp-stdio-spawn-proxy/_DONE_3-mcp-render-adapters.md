# Step 3: IDE adapters render spawn wrapper when `spawn_stdio_proxy`

Canonical implementation notes: **`overview.md`**, section **Implementation details** (**`spawn`** **`command`**, **`mcp_stdio_argv`**, adapter file list).

## Goal
Whenever **`spawn_stdio_proxy`** is **true** and transport is **`stdio`**, adapters emit **stable **`command`** + **`args`**** reflecting **`spawn mcp_stdio extension <extension> name <name>`**, not raw **`transport.command`** / **`args`**.

## Approach
1. Implement **`spawn_cli.ide.mcp_stdio_argv`** (**signature** **`overview.md`**) once; adapters import it.
2. **`command`**: **`"spawn"`** only (**`overview.md`**); no dynamic Python interpreter selection in rendered MCP.
3. For each MCP-capable **`IdeAdapter`** emitting **`stdio`** (**`overview.md`** file list; **`zed`** is out of scope) update **`_build_*`** / **`add_mcp`**: the **`spawn_stdio_proxy`** branch mirrors non-proxy **`stdio`** output (**`env`/`cwd`/`inputs`**) except **`command`/`args`**.
4. **Golden tests**: diff only **`command`/`args`** vs baseline (**overview.md** Regression tests).
5. **Non-proxy**: untouched.

## Affected files
- **`spawn_cli/ide/**/*.py`** (all **`add_mcp`** stdio builders)
- Optional shared helper:**`spawn_cli/ide/_mcp_stdio_render.py`** (name illustrative)

## Code examples

```python
ARGS = ["mcp_stdio", "extension", srv.extension, "name", srv.name]
```

Illustrative (full shape depends on adapter; non-wrapper fields mirror plain **`stdio`**):

```json
{
  "mcpServers": {
    "spectask-search": {
      "command": "spawn",
      "args": ["mcp_stdio", "extension", "spectask", "name", "spectask-search"],
      "cwd": ".",
      "env": {"SOME_TOKEN": "${SOME_TOKEN}"}
    }
  }
}
```
