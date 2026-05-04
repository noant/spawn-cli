---
name: mempalace-diagnose-palace
description: Diagnose MemPalace install, palace path alignment, CLI/MCP, and wake-up context in the target repo.
---


When the user reports **MemPalace not working**, **empty search**, **MCP errors**, or **stale context**:

1. **Pack / Python**
   - Run **`spawn extension healthcheck mempalace`** (or `healthcheck.py` with the same Python Spawn uses). Failure → install **`mempalace`** in **that exact interpreter** (the healthcheck prints it). If **`python -c "import mempalace"`** in your shell works but healthcheck exits 1, Spawn is using a different Python — align them or install into the interpreter Spawn uses.
   - Use **`.mempalace/ext/requirements-mempalace.txt`** and `after_install.py` skip flags **`MEMPALACE_EXTENSION_SKIP_PIP`** / **`MEMPALACE_EXTENSION_SKIP_INIT`** as needed.
   - From the **repo root**, run **`python -c "import mempalace"`** and **`python -m mempalace --version`** (or **`py -m mempalace`** on Windows if that is the configured interpreter).

2. **Palace initialized and healthy**
   - If there is no project scaffold, run **`mempalace init .`** from the repo root (or rely on the after-install hook). Confirm **`.mempalace/`** and project **`mempalace.yaml`** (and **`entities.json`** if used) exist.
   - **Extension-only tree:** if `.mempalace/` only has **`guides/`**, **`ext/`**, **`wakeup.md`** and almost no mined layout, indexing was never completed — run **`mempalace mine .`** after a good **`init`** (and fix palace path alignment first).
   - **Broken store:** **`mempalace search`** reporting *No palace found* or **`mempalace repair-status`** showing unreadable state / zero counts while `chroma.sqlite3` exists usually means corrupted or mismatched palace data vs CLI version — try upstream **`repair`** / **`repair --dry-run`**, or after backup **`mempalace init .`** + **`mine`** for a clean repo-local palace.

3. **Same palace everywhere**
   - Compare **`palace_path`** in **`~/.mempalace/config.json`**, repo **`mempalace.yaml`**, **`MEMPALACE_PALACE_PATH`**, **this extension’s default `<repo>/.mempalace/palace`**, and any **`--palace`** / MCP server args. Misalignment causes “nothing found” or tools touching the wrong store — see **`.mempalace/guides/configuration.md`**.
   - On Windows, normalize **`palace_path`** to a consistent form (prefer all backslashes `\\` or a single POSIX style) — mixed separators alone can confuse tools or editors but the real symptom is mismatched dirs; merged MCP env sets **`MEMPALACE_PALACE_PATH`** for **`mempalace-mcp`** when not overridden — align CLI search with that path.

4. **CLI smoke test**
   - **`mempalace search "<known phrase>"`** using the same **`--palace`** / env the IDE will use. If this fails, fix paths or init before debugging MCP.

5. **MCP**
   - Both **`mempalace-mcp`** and **`mempalace-mine-mcp`** must use a **`python` / `mempalace`** that has the package installed (often venv / **`py`** on Windows). **`mempalace-mcp`** must launch **`mempalace.mcp_server`** (**`python -m mempalace.mcp_server`**, or **`mempalace-mcp`**); if the merged config mistakenly uses **`python -m mempalace mcp`**, tools never appear (**connection closed** / **-32000**) — that subcommand is setup text only.
   - After **`mempalace_mine`** succeeds, **`.mempalace/wakeup.md`** should update; if the main server was already up, call **`mempalace_reconnect`** on **`mempalace-mcp`**. Full checklist: **`.mempalace/guides/guide.md`** (MCP + IDE wiring).

6. **Narrow the symptom**
   - Import/CLI failure → step 1–2. Search works in terminal but not in IDE → step 3–5. Wake-up outdated → mine + reconnect and verify **`wakeup.md`**.

For **changing** wings, rooms, paths, or identity, use skill **mempalace-configure-palace** instead of repeating full diagnostics.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.

Mandatory reads:
- `.mempalace/guides/guide.md` - MemPalace in the target repo — install, init, MCP mine/wake-up workflow, links to official docs.
- `.mempalace/guides/configuration.md` - Reference for config.json, mempalace.yaml, env vars, and repo-local palace_path.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
