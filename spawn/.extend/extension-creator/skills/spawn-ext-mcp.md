---
name: spawn-ext-mcp
description: >-
  Add or edit Spawn extension MCP under extsrc/mcp/ — three platform JSON files
  (windows, linux, macos), servers shape, aligned server names, optional
  spawn_stdio_proxy for stdio indirection, and safe env handling.
---

Goal: declare MCP servers bundled with the extension so Spawn merges them per host OS into IDE configs.

### Layout

- Use **`extsrc/mcp/windows.json`**, **`extsrc/mcp/linux.json`**, **`extsrc/mcp/macos.json`** only (`spawn extension init` scaffolds all three as `{"servers": []}`).
- **Do not** add **`extsrc/mcp.json`** — obsolete; **`spawn extension check`** flags it.

### Editing workflow (add or change servers)

1. **Plan globally unique **`servers[].name`** values** across every extension that might install beside this one in the same target (prefer prefixed ids, e.g. `myorg-docs-mcp`).
2. **Keep the server `name` set identical** in all three JSON files (same names; order may differ per file).
3. For each OS file, edit the **`servers`** array with the Spawn shape: top-level **`servers`** — not IDE **`mcpServers`**.
4. **`transport`**: default mental model **`stdio`** with **`command`** / **`args`** / **`cwd`**; **`sse`** / **`streamable-http`** use **`url`** where the adapter supports that **`type`**.
5. **`spawn_stdio_proxy`** (optional boolean, default **`false`**): when **`true`**, **`transport.type`** **must** be **`stdio`**. Spawn **does not** copy the inner **`command`** / **`args`** into the IDE’s project MCP file. Instead, adapters emit a single stable launcher: IDE **`command`** **`spawn`** with **`args`** that run **`mcp_stdio`** and point at this extension’s install id (**`extension`**) and this server’s **`name`**. The real stdio command stays in the pack; the repo only sees the proxy. **`spawn extension check`** errors if **`spawn_stdio_proxy`** is **`true`** with a non-stdio **`transport`**. Use it when you want small, stable committed MCP configs and to ship command-line changes only with the extension. Keep the flag **the same** for a given **`name`** across **`windows.json`**, **`linux.json`**, and **`macos.json`** so the same server doesn’t mean different launch modes per OS.
6. **`env`**: never commit secrets; structured objects with **`secret`** / **`required`**, or non-object placeholders — generated IDE config uses placeholders for user values.
7. **`capabilities`**: set when defaults (tools on, resources/prompts off) are wrong for the server.
8. When transport truly differs by OS (e.g. **`python`** vs **`python3`**, or Windows-specific exe), duplicate the server **`name`** in each file but adjust only **`transport`** (and **`env`** if needed) per platform.
9. **Homogeneous setups:** duplicate the **same** JSON payload into **`windows.json`**, **`linux.json`**, and **`macos.json`** if all three match — still three files required.
10. Run **`spawn extension check .`** (`--strict` in CI): parsing, stray obsolete **`extsrc/mcp.json`**, **matching `name`** sets across **`extsrc/mcp/*.json`**, and **`spawn_stdio_proxy`** ↔ **`stdio`** consistency.

### Release discipline

Changing **`servers`**, transports, **`spawn_stdio_proxy`**, **`env`** contract, or **`capabilities`** is consumer-visible MCP behavior — **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before publishing.
