Wake-up text (~796 tokens):
==================================================
## L0 — IDENTITY
No identity configured. Create ~/.mempalace/identity.txt

## L1 — ESSENTIAL STORY

[mempalace]
  - <!-- spawn:start --> Before working, read `spawn/navigation.yaml`. Read every file listed under `read-required`. Inspect `read-contextual` descriptions and read only files relevant to the current t...  (AGENTS.md)
  - {   "mcpServers": {     "mempalace-mcp": {       "command": "spawn",       "args": [         "mcp_stdio",         "extension",         "mempalace-ext",         "name",         "mempalace-mcp"      ...  (mcp.json)
  - --- name: mempalace-configure-palace description: Configure MemPalace for a repo-local palace (YAML, palace_path, identity, room merges/splits, alternate slices with apply flow). ---     When the u...  (SKILL.md)
  - otes on **`~/.mempalace/config.json`**, **`MEMPALACE_EXTENSION_GLOBAL_PALACE`**, and other overrides live in **`.mempalace/guides/configuration.md`** — **do not** open a competing “prefer global pa...  (SKILL.md)
  - ote for ignores), **`tests`** / **`spec`**, infra (`infra`, `deploy`, `.github`), and docs (`docs`).     - **Primary mapping (topology cut):** group **wings** at the grain of loosely coupled subtre...  (SKILL.md)
  - opose adjusting granularity so the palace tracks how humans navigate the repo, not duplicating junk:       - **Merge candidates** — folders or existing rooms whose **labels or roles overlap** by na...  (SKILL.md)
  - ementation). Prefer one room per cohesive navigational locus unless separation clarifies onboarding.       - **Split candidates** — a single directory that **bundles unrelated concerns by name** (m...  (SKILL.md)
  - rms), adjust room keys and paths together so **`mempalace search`** and mental map stay predictable.       - Deliver a short **reshape plan**: bullets like **merge →** one room target, **split →** ...  (SKILL.md)
  - iffer.       - **Layer or concern** — API vs domain core vs adapters vs persistence vs presentation.       - **Lifecycle / artifact type** — production runtime vs tooling & scripts vs CI vs fixture...  (SKILL.md)
  - palace_mine`** will use **`wing`** when mining additional slices (**`.mempalace/guides/guide.md`**).     - **Immediate apply path for slices:** When the topology default or **any alternate cut** is...  (SKILL.md)
  - **`mine`** (and MCP **`mempalace_reconnect`** when the main server stays hot across layout changes).     - If the repo is tiny or flat, propose a minimal 1‑wing scaffold and revisit after growth.  ...  (SKILL.md)
  - palace mine .`**; later changes to paths or wing/room layout usually imply running **`mine`** again.  4. For multilingual entity extraction when needed, set **`MEMPALACE_ENTITY_LANGUAGES`** (see Py...  (SKILL.md)
  - nsions UI — labels differ by Cursor/VS Code lineage — then reload/restart MCP per vendor guidance.    Keep secrets and personal data out of static extension templates; do not commit private memory ...  (SKILL.md)
  - alace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.  Mandatory reads: - `.mempalace/guides/guide.md` - MemPalace in the target repo — install, init,...  (SKILL.md)

[spawn]
  ... (more in L3 search)
