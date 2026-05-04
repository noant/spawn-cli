# Step 1: Schema, models, parsing, validation

Canonical implementation notes: **`overview.md`**, section **Implementation details** (JSON **`spawn_stdio_proxy`**, **`McpServer`** field, **`extension_check`**).

## Goal
Represent **`spawn_stdio_proxy`** on normalized MCP servers, parse it from extension **`mcp/{platform}.json`**, enforce **`extension_check`** rules, without changing **`list_mcp`** call sites beyond field availability.

## Approach
1. Extend **`McpServer`** (**`spawn_cli.models.mcp`**) with **`spawn_stdio_proxy: bool = False`**.
2. In **`spawn_cli.core.low_level._normalized_mcp_from_loaded`** (**or equivalent**): read optional boolean from raw server dict; normalize case/legacy absent **`->`** **`False`**.
3. **`extension_check`** **(high_level)**:
   - If **`spawn_stdio_proxy`** and **`transport.type` != **`stdio`** **->** actionable error (**strict**/non-strict per existing MCP validation pattern).
   - Optional: Warn if **`proxy`** true but inner **`command`** empty (should already be invalid today).
4. Keep **`list_mcp`** semantics: **always** resolves current OS file; callers see full transport plus flag.

## Affected files
- **`spawn_cli/models/mcp.py`**
- **`spawn_cli/core/low_level.py`**
- **`spawn_cli/core/high_level.py`** (extension check MCP branch)
- **`tests/core/test_low_level.py`** or new focused test module for MCP parsing

## Code examples

```python
# models/mcp.py (shape only)
class McpServer(BaseModel):
    ...
    spawn_stdio_proxy: bool = Field(default=False, alias="spawn_stdio_proxy")  # or populate_by_name
```

```yaml
# extsrc/mcp/linux.json excerpt
servers:
  - name: my-tool
    spawn_stdio_proxy: true
    transport:
      type: stdio
      command: uvx
      args: ["some-mcp-package"]
```
