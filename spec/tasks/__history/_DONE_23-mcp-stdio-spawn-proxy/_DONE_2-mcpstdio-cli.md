# Step 2: `spawn mcp_stdio` CLI command and stdio proxy

Canonical implementation notes: **`overview.md`**, section **Implementation details** (parser nesting, **`_dispatch`** **`spawn_lock`** bypass, runtime relay, **`Popen`** / threading).

## Goal
Implement **`spawn mcp_stdio extension <id> name <server>`**: resolve repo root, locate server by name for current OS, spawn inner stdio MCP with MCP-compatible **stdin/stdout** relay (and deterministic **stderr** behavior per overview).

## Approach
1. **Argparse wiring** (**`spawn_cli.cli`**): nested **literal** tokens **`extension`** … **`name`** as in overview.
2. **Lock / buffering / stderr**: Follow **CLI proxy implementation details** in **`overview.md`** (prefer **no** **`spawn_lock`**; binary-safe unbuffered stdio forwarding; forward inner **`stderr`**).
3. **Resolver helper** (**`spawn_cli.core.high_level`** or a small **`core/mcp_stdio.py`** module): **`target_root = Path.cwd().resolve()`**; **`_require_init`**, load **`list_mcp(target_root, extension_id)`**, find **`McpServer.name == server_name`**, verify **`transport.type == stdio`**, **`spawn_stdio_proxy`** is **True** (**error** otherwise with clear UX).
4. **Subprocess / stdio bridging**: **`subprocess.Popen`** (or **`asyncio`**) matching **overview** buffering rules.
5. **Inner cwd and env**: **`Popen`** with **`cwd`** from normalized transport; merge **`env`** from **`McpEnvVar`** + **`os.environ`** (IDE injects placeholders into **`spawn`** so **`os.environ`** already reflects resolved secrets where applicable).

## Affected files
- **`spawn_cli/cli.py`**
- New **`spawn_cli/core/...`** module if bridging logic is non-trivial (**otherwise** **`high_level`** with a thin wrapper).
- **`tests/`**: heavy coverage may land in **`4-tests-validation.md`**; keep one smoke path here if convenient.

## Code examples

```text
spawn mcp_stdio extension spectask name spectask-search
```

```python
# Pseudocode guard
srv = pick_server(nm, server_name)
if not srv.spawn_stdio_proxy or srv.transport.type != "stdio":
    raise SpawnError("server is not configured for spawn stdio proxy")
```
