---
document: spawn-extension-mcp-json
audience: machine
encoding: utf-8
prerequisite: spawn-ext-guide/ai/core.md (global uniqueness of server names)
---

# extsrc/mcp/*.json — machine schema (per platform)

paths (extension source **only**; not merged into arbitrary IDE JSON by hand — Spawn adapters emit IDE-specific config):

- **`extsrc/mcp/windows.json`**
- **`extsrc/mcp/linux.json`**
- **`extsrc/mcp/macos.json`**

constraint: **all three files** MUST exist when MCP is authored; each MUST be valid JSON.

obsolete:

- **`extsrc/mcp.json`** is NOT read; **`spawn extension check`** reports it if present.

selection_and_merge:

- Spawn picks **one** file for the **host OS** when normalizing MCP for rendering.
- The **logical** MCP contract for the extension is the **union** of the three files subject to **`platform_name_alignment`** below.

platform_name_alignment:

- The **set** of server **`name`** values MUST be **identical** in all three JSON files (**order MAY differ** per file).
- **`transport`**, **`env`**, **`capabilities`** MAY differ per platform when commands or URLs differ by OS.

format_note:

- Each file uses top-level **`servers`** array (NOT IDE root **`mcpServers`** object); Spawn normalizes; adapters rewrite per IDE.

## top_level

| field | type | semantics |
|-------|------|-----------|
| servers | array | each element one MCP server; `[]` allowed when all three files share empty name set |

## server_object

| field | type | required | semantics |
|-------|------|----------|-----------|
| name | string | yes | stable id; MUST be unique across ALL extensions in same target |
| spawn_stdio_proxy | bool | no | default `false`; when `true`, stdio proxy semantics apply; see spawn_stdio_proxy_semantics |
| transport | object | implicit default | connection; omit → parser defaults (`type` default `stdio`) |
| env | object | no | env vars; see env_semantics |
| capabilities | object | no | see capabilities_defaults |

## spawn_stdio_proxy_semantics

purpose: keep **generated IDE project MCP** free of the extension’s inner **`transport.command`** / **`args`** while still running a stdio MCP server.

rules:

- If **`spawn_stdio_proxy`** is **`true`**: **`transport.type`** MUST be **`stdio`**. Adapters emit IDE MCP with **`command`**: **`spawn`** and **`args`** that invoke **`mcp_stdio`** with **`extension`** (installed extension directory id) and **`name`** (this server’s **`name`**). Inner **`command`**, **`args`**, **`cwd`** remain in extension metadata only; Spawn resolves them at launch.
- If **`spawn_stdio_proxy`** is **`false`** or **omitted** (default): IDE config MAY include the normalized **`transport`** directly (adapter-dependent), subject to usual rewriting.
- Remote transports (**`sse`**, **`streamable-http`**, URL-based): **`spawn_stdio_proxy`** MUST NOT be **`true`**; **`spawn extension check`** MUST flag **`spawn_stdio_proxy`** with non-stdio **`transport`**.

authoring_note:

- For one logical server (same **`name`**), use the **same** **`spawn_stdio_proxy`** value in **`windows.json`**, **`linux.json`**, and **`macos.json`** so behavior does not diverge by OS.

## transport_fields

| field | default | semantics |
|-------|---------|-----------|
| type | `"stdio"` | `stdio`, `sse`, `streamable-http`, etc. per adapter mapping |
| command | — | executable for stdio |
| args | `[]` | string list |
| cwd | `"."` | working directory |
| url | — | for HTTP/SSE when type not plain stdio |

## env_value_semantics

- **A** non-object scalar, or JSON value not a mapping → user secret → IDE placeholder (never literals in repo).
- **B** mapping → optional fields:

| field | type | default | semantics |
|-------|------|---------|-----------|
| source | string | `"user"` | provenance |
| required | bool | `true` | var must be set |
| secret | bool | `false` | mask/placeholder in generated config |
| value | string \| null | null | non-secret default when secret false |

## capabilities_defaults

| field | default |
|-------|---------|
| tools | true |
| resources | false |
| prompts | false |

## validation

- `spawn extension check`: all three files present under `extsrc/mcp/` (when MCP is expected), JSON parse, **matching** server **`name`** sets across platforms, stray **`extsrc/mcp.json`** reported; **`spawn_stdio_proxy: true`** MUST pair with **`transport.type`** **`stdio`** (or default stdio); semantic issues MAY surface when MCP is loaded for rendering.

## examples.reference_only

body note: snippets are the **contents of one** platform file (`windows.json` \| `linux.json` \| `macos.json`). For production, replicate the **same** `servers` list into **all three** files when transports match, or adjust **`transport`** per file only where OS differs.

example_stdio_spawn_proxy:

```json
{
  "servers": [
    {
      "name": "acme-docs-mcp",
      "spawn_stdio_proxy": true,
      "transport": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@acme/mcp-server", "--stdio"],
        "cwd": "."
      },
      "capabilities": { "tools": true, "resources": false, "prompts": false }
    }
  ]
}
```

body note: after install, IDE MCP shows **`spawn`** + **`mcp_stdio`** targeting this extension and **`acme-docs-mcp`**; inner **`npx`** line is not written into the project MCP file.

example_stdio_secret_object:

```json
{
  "servers": [
    {
      "name": "acme-docs-mcp",
      "transport": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@acme/mcp-server", "--stdio"],
        "cwd": "."
      },
      "env": {
        "ACME_API_TOKEN": {
          "source": "user",
          "required": true,
          "secret": true
        }
      },
      "capabilities": { "tools": true, "resources": false, "prompts": false }
    }
  ]
}
```

example_streamable_http:

```json
{
  "servers": [
    {
      "name": "acme-remote-mcp",
      "transport": { "type": "streamable-http", "url": "https://mcp.example.com/v1" },
      "capabilities": { "tools": true, "resources": false, "prompts": false }
    }
  ]
}
```

example_sse:

```json
{
  "servers": [
    {
      "name": "acme-sse-gateway",
      "transport": { "type": "sse", "url": "https://mcp.example.com/sse" }
    }
  ]
}
```

example_python_stdio:

```json
{
  "servers": [
    {
      "name": "acme-python-mcp",
      "transport": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "acme_mcp", "--stdio"],
        "cwd": "."
      }
    }
  ]
}
```

uv_wrapper_fragment (replace command/args as needed):

```json
"command": "uv",
"args": ["tool", "run", "acme-mcp-cli", "--stdio"]
```

example_minimal_stdio:

```json
{
  "servers": [
    {
      "name": "pack-minimal-stdio",
      "transport": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@some-scope/some-mcp-package"]
      }
    }
  ]
}
```

example_two_servers:

```json
{
  "servers": [
    {
      "name": "methodology-docs-mcp",
      "transport": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@org/mcp-docs", "--stdio"]
      }
    },
    {
      "name": "methodology-lint-mcp",
      "transport": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@org/mcp-lint", "--stdio"]
      }
    }
  ]
}
```

example_env_plain_placeholder:

```json
{
  "servers": [
    {
      "name": "pack-with-inline-env-hint",
      "transport": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@org/mcp-server"]
      },
      "env": { "ORG_API_KEY": "" }
    }
  ]
}
```

note: empty string still marks placeholder in many adapters; prefer explicit object form in example_stdio_secret_object for `required` / `secret`.
