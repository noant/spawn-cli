---

name: mempalace-configure-palace

description: Configure MemPalace for a repo-local palace; propose wing/room layout from repo structure, reshape rooms after name/topology analysis, negotiate alternate slices with concrete YAML deltas and consent, align MCP/tooling paths.

---



When the user wants **palace configuration** (wings, rooms, paths, entities, identity):



1. **Treat the palace as repo-local.** This workflow assumes **`mempalace.yaml`** plus data under **`<repo>/.mempalace/palace`**, aligned with this pack’s MCP **`env`** (**`MEMPALACE_PALACE_PATH=.mempalace/palace`**) when clients use merged config from **`spawn extension add`**. For **`mempalace search`** (plain terminal), set **`MEMPALACE_PALACE_PATH`** or **`--palace`** to the **same directory** MCP uses. Technical notes on **`~/.mempalace/config.json`**, **`MEMPALACE_EXTENSION_GLOBAL_PALACE`**, and other overrides live in **`.mempalace/guides/configuration.md`** — **do not** open a competing “prefer global palace” UX here.

2. **Propose an optimal palace sketch from the codebase** before locking `mempalace.yaml` (adapt names to upstream schema after `mempalace init` / official docs):

   - **Inventory:** scan top-level tree, README, manifests (`pyproject.toml`, `package.json`, workspace files), dominant `src`/`app`/`lib`/`internal`/`packages` layouts, generated/vendor dirs (note for ignores), **`tests`** / **`spec`**, infra (`infra`, `deploy`, `.github`), and docs (`docs`).

   - **Primary mapping (topology cut):** group **wings** at the grain of loosely coupled subtrees or packages; assign **rooms** to coherent folders or modules (consistent naming — short ASCII labels readable in MCP). Prefer few wide wings over dozens of microscopic ones unless the repo is huge and domain-driven.

   - **Reshape rooms from your own naming analysis** — after inventory + primary mapping (and **`mempalace.yaml`** if it already exists), explicitly propose adjusting granularity so the palace tracks how humans navigate the repo, not duplicating junk:

     - **Merge candidates** — folders or existing rooms whose **labels or roles overlap** by name convention (e.g. `tests` / `spec` / `__tests__`, `app` / `frontend` / `web`, duplicated `*-service` stubs, thin wrappers sitting next to the real implementation). Prefer one room per cohesive navigational locus unless separation clarifies onboarding.

     - **Split candidates** — a single directory that **bundles unrelated concerns by name** (many sibling packages, `internal/` with orthogonal domains, mega-`packages/` subtrees): propose **multiple rooms** (or subtrees under one wing with distinct room paths) keyed off clear name prefixes / package boundaries evident from the tree and manifests.

     - **Rename / align** — when a proposed room label **does not match** repo language (camel vs kebab vs domain terms), adjust room keys and paths together so **`mempalace search`** and mental map stay predictable.

     - Deliver a short **reshape plan**: bullets like **merge →** one room target, **split →** list of room paths + rationale grounded in observed names—not generic advice. If the sketch already fits, say so briefly.

     - Structural changes to wings/rooms after **`mine`** imply **mining again**; call that out when proposing merges/splits/renames.

   - **Alternate cuts** — offer at least **two extra views** beside the topology default, briefly compare trade-offs:

     - **Domain / bounded context** — wings by product capability (billing, identity, ingestion) even when folders differ.

     - **Layer or concern** — API vs domain core vs adapters vs persistence vs presentation.

     - **Lifecycle / artifact type** — production runtime vs tooling & scripts vs CI vs fixtures vs documentation.

     - Optionally **ownership** (`CODEOWNERS`, team prefixes) when it explains real navigation.

   - **Recommend one default** for **`mempalace.yaml`** and first **`mine`**: the cut that best matches where humans already look plus MemPalace’s loci metaphor; note if **`mempalace_mine`** will use **`wing`** when mining additional slices (**`.mempalace/guides/guide.md`**).

   - **Immediate apply path for slices:** When the topology default or **any alternate cut** is chosen, summarize it as concrete edits before touching disk — proposed **`wing`**, ordered **`rooms`**, **`palace_path`** if relevant, secondary **`wing`**/`mempalace_mine` passes when that slice warrants it (constraints on **`directory`**, **`mode`**, **`wing`**, **`palace`** remain per **guide**). **Ask once**: whether to apply those changes to **`mempalace.yaml`** / **`entities.json`**; on confirmation, patch the workspace files accordingly; remind **`mine`** (and MCP **`mempalace_reconnect`** when the main server stays hot across layout changes).

   - If the repo is tiny or flat, propose a minimal 1‑wing scaffold and revisit after growth.

3. Edit or create project files after `mempalace init`:

   - **`mempalace.yaml`** — wing, room list (labels — **not** file paths in YAML), optional `palace_path`. For **which directory to mine** per slice, see **`.mempalace/guides/configuration.md` → “Rooms vs repo paths (for agents)”** and MCP **`mempalace_mine`**’s **`directory`** argument.

   - **`entities.json`** — name mappings for the project.

   - Prefer locking **`palace_path`** + project YAML / entities **before** the first **`mempalace mine .`**; later changes to paths or wing/room layout usually imply running **`mine`** again.

4. For multilingual entity extraction when needed, set **`MEMPALACE_ENTITY_LANGUAGES`** (see PyPI / upstream docs for your installed version).

5. Sanity-check alignment: run `mempalace search "<phrase>"` with the same **`--palace`**/env that MCP uses.

6. For IDE MCP wiring (servers, PATH, reload), follow **`.mempalace/guides/guide.md`** — **MCP servers** and **IDE wiring checklist**. If merged config landed but listing tools stays empty / failing, remind the human to turn **on** MCP (or enable each spawned server entry) inside the IDE’s MCP or extensions UI — labels differ by Cursor/VS Code lineage — then reload/restart MCP per vendor guidance.



Keep secrets and personal data out of static extension templates; do not commit private memory maps unless the team explicitly chooses to.

