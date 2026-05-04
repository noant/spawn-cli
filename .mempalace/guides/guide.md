# MemPalace in this repository

[MemPalace](https://pypi.org/project/mempalace/) is local-first memory for assistants: verbatim storage and semantic search (method of loci: wings → rooms → halls → drawers). Official docs: [getting started](https://mempalaceofficial.com/guide/getting-started), [configuration](https://mempalaceofficial.com/guide/configuration.html).

## What this extension teaches

1. Install the package and CLI into the developer environment (via **`after_install.py`** or manually).
2. Initialize a **palace** scoped to the **root of the current repository** — **`mempalace init .`** (the hook runs **`mempalace init .`** interactively after install when not skipped, with Spawn forwarding hook I/O).
3. Align global and project config so search, mining, and MCP all use the same `palace_path`.
4. Optionally enable MCP (this pack declares servers under **`extsrc/mcp/`** — **`windows.json`**, **`linux.json`**, **`macos.json`**; after **`spawn extension add`**, Spawn merges the file matching the host OS).

## MCP servers

This extension ships two stdio MCP servers (see **`extsrc/mcp/*.json`**); each merges **`MEMPALACE_PALACE_PATH=.mempalace/palace`** (**repo-local Chroma**) relative to **`cwd`**.

Unicode (including Cyrillic) over MCP JSON-RPC is handled by enabling **CPython UTF-8 mode** via **`-X utf8`** in every platform file’s **`transport.args`** (**`py -3 -X utf8 …`** on Windows, **`python3 -X utf8 …`** on Linux/macOS). Do **not** put **`PYTHONIOENCODING`** in pack **`env`**: when **`spawn_stdio_proxy`** merges into IDE MCP, some adapters rewrite it as **`${PYTHONIOENCODING}`** without resolving it, which crashes Python (**`unknown encoding: ${PYTHONIOENCODING}`**). Do **not** set **`PYTHONUTF8`** in merged **`env`** either — invalid merged values trigger **`invalid PYTHONUTF8`** at interpreter startup; **`-X utf8`** avoids that. If searches still misbehave after that, rule out upstream **`mempalace`** / embedding behavior separately from this pack.

| Server id | Purpose |
|-----------|---------|
| **`mempalace-mcp`** | Official MemPalace stdio server: **`py -3 -X utf8 -m mempalace.mcp_server`** (Windows pack defaults) or **`python3 -X utf8 -m mempalace.mcp_server`** (Linux/macOS): search, drawers, graph, diary, etc. No **`Scripts`** shim on **`PATH`** required (**`mempalace-mcp`** is the upstream console entry if you wire it manually elsewhere). **`mempalace mcp`** / **`python -m mempalace mcp`** is CLI *setup/help only* — it prints instructions and exits; hosts must run **`mempalace.mcp_server`** over stdio for MCP tools. |
| **`mempalace-mine-mcp`** | Thin bridge: tool **`mempalace_mine`** runs **`mempalace mine`** via **`py -3 -X utf8`** / **`python3 -X utf8`** + **`.mempalace/ext/mine_mcp_server.py`** with workspace **`cwd`** (interpreter name matches the platform file). |

Both servers must use an interpreter where the **`mempalace`** package is installed (same venv as your terminal, or override **`command`** in the IDE adapter). On Windows, if **`python`** is missing, use **`py`** or a full venv **`python.exe`** path in your override for **both** servers together.

For **`mempalace-mine-mcp`**, the tool **`mempalace_mine`** only accepts **`directory`**, **`mode`**, **`wing`**, and **`palace`** — other `mempalace mine` flags stay CLI-only.

After a successful **`mempalace_mine`**, this bridge also runs **`mempalace wake-up`** (same **`palace`** / **`wing`** as the mine call) and overwrites **`.mempalace/wakeup.md`** with that context. Then call **`mempalace_reconnect`** on **`mempalace-mcp`** if the main server was already running and you need it to see on-disk palace updates immediately.

### IDE wiring checklist

After **`spawn extension add`**, Spawn merges this pack’s **`extsrc/mcp/<platform>.json`** into the target’s MCP config — keep server **`name`** values unique across all extensions in that target.

Confirm both server processes see a Python environment where **`mempalace`** is installed (same venv as your terminal, or adjust the adapter’s **`command`** / **`args`** consistently for **both** servers). Pack defaults: **`command`** is **`py`** on Windows and **`python3`** on Linux/macOS; **`mempalace-mcp`** uses **`py -3 -X utf8 -m mempalace.mcp_server`** (**`python3 -X utf8 …`** on Unix). Override if your host only exposes **`python`** on Unix, or a venv **`python.exe`** on Windows. For human-readable MCP wiring hints run **`mempalace mcp`** or **`python -m mempalace mcp`** in a terminal; that CLI subcommand does not start the MCP protocol.

After changing MCP config or env vars, restart MCP / the IDE per client rules and verify tools are listed (**`mempalace_mine`** on **`mempalace-mine-mcp`**). If nothing appears despite a valid merged config, check the IDE’s MCP or extensions toggles — some shells keep servers disabled until explicitly enabled.

Official tool list: [mempalaceofficial.com](https://mempalaceofficial.com/).

## Spawn setup hooks

When Spawn materializes this pack (**`spawn extension add`** / **`spawn extension update mempalace`**), it **runs** **`after_install.py`** because **`setup.after-install`** is set in the extension `config.yaml`. The script:

1. Runs **`pip install mempalace==<pinned>`** using the **same Python** that executes the hook (not necessarily your day-to-day venv), unless **`MEMPALACE_EXTENSION_SKIP_PIP=1`** (or `true` / `yes`). If that Python has no `pip` module, the script falls back to **`uv pip install --python=...`** when `uv` is on `PATH`.
2. Runs **`mempalace init .`** in the **current working directory** (expect the target repo root), unless **`MEMPALACE_EXTENSION_SKIP_INIT=1`**. The **`init`** subprocess inherits Spawn’s stdin/stdout/stderr so you can confirm entities and respond to prompts (e.g. “mine now?”). For **`init`** (and **`--auto-mine`** when enabled), **`MEMPALACE_PALACE_PATH`** is set to **`<repo>/.mempalace/palace`** when not already exported and unless **`MEMPALACE_EXTENSION_GLOBAL_PALACE`** opts into MemPalace’s default **`~/.mempalace/palace`**. To mine immediately without that prompt flow, set **`MEMPALACE_EXTENSION_AUTO_MINE=1`** (adds **`--auto-mine`**; can take a long time on large trees).

You can verify the package with **`spawn extension healthcheck mempalace`** when `healthcheck` is configured in this pack. On failure it prints stderr *and* stdout (including **`sys.executable`**) — if **`python -c "import mempalace"`** works in your shell but healthcheck fails, Spawn is using a different interpreter; install **`mempalace`** into that interpreter.

## Manual quick path

If you set **`MEMPALACE_EXTENSION_SKIP_PIP`** / **`MEMPALACE_EXTENSION_SKIP_INIT`**, or use a different environment than the hook’s Python:

```bash
pip install -r .mempalace/ext/requirements-mempalace.txt
cd /path/to/this/repo
mempalace init .
```

Then edit `~/.mempalace/config.json` and/or project `mempalace.yaml`, `entities.json` using the [configuration reference](./configuration.md).

## File namespace

- **`.mempalace/guides/`** (this file and [configuration](./configuration.md)) — **extension-local mandatory reads only** (`localRead: required`): injected into this pack’s rendered skills; **not** in global Spawn navigation. Extension MCP bridge: **`.mempalace/ext/mine_mcp_server.py`**.
- **`.mempalace/wakeup.md`** — **global mandatory read** via Spawn navigation: bounded wake-up context refreshed by **`mempalace_mine`** after a successful mine or by **`mempalace wake-up`**; ships as an artifact stub until then.
- Palace data after `init`: usually **`.mempalace/`** at the repo root — other tree layout depends on your CLI version.

Use skills: **mempalace-configure-palace** (palace YAML, paths, entities; MCP details are above), **mempalace-diagnose-palace** (install, palace alignment, CLI/MCP, wake-up troubleshooting).
