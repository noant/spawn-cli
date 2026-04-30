# Utility module flows (depth reference)

This document complements `spec/design/utility.md`: for each logical module it
states **inputs**, **how data is read or produced**, **outputs / persistence**, and
**semantics**. Names follow the kebab-case identifiers from `utility.md`;
implementations typically map them to `snake_case` in code.

Paths are relative to **target repository root** unless noted. **Lock:** **every**
CLI command acquires `spawn/.metadata/.spawn.lock` **non-blocking** before doing
any work; if acquisition fails, **`SpawnError`** including **`Операция в
процессе (файл lock detected)`**. There is no lock-free fast path.

**Initialization:** any command other than `spawn init` must verify `spawn/`
exists; otherwise **`SpawnError`** including **`need init before`**.

---

## 1. `supported_ide_keys()`

| Aspect | Detail |
| --- | --- |
| **Reads** | No I/O. **Implementation:** one module-level `CANONICAL_IDE_KEYS`
tuple/list in source defines **both** order and membership; no env vars, no
config files. |
| **How** | Return that constant. Registry code must register a **concrete** adapter for every key. |
| **Writes** | None. |
| **Meaning** | Same ordered list drives `detect_supported_ides` iteration and `spawn ide list-supported-ides` YAML key order. |

---

## 2. `detect_supported_ides(targetRoot)`

| Aspect | Detail |
| --- | --- |
| **Reads** | For each key from `supported_ide_keys()`, the registered `IdeAdapter` instance; adapter `detect(targetRoot)` inspects the repo tree (marker files, config dirs). |
| **How** | `ide.Get(key).detect(targetRoot)` — no extension or navigation reads. |
| **Writes** | None. |
| **Meaning** | Diagnostics and `spawn ide list-supported-ides`: report whether each IDE “looks used” in this repo and what surfaces (`skills`, `mcp`, `agentIgnore`, `entryPoint`) the adapter can render. |

---

## 3. `init()`

| Aspect | Detail |
| --- | --- |
| **Reads** | Packaged CLI template for default `spawn/.core/config.yaml` (`importlib.resources` or equivalent). |
| **How** | Create missing directories/files idempotently. |
| **Writes** | `spawn/`, `spawn/.core/config.yaml`, `spawn/.metadata/ide.yaml`, `spawn/.metadata/git-ignore.txt`, `spawn/rules/`, `spawn/navigation.yaml`; Spawn-managed **root** `.gitignore` entry for `spawn/.metadata/temp/` (see `utility.md` Temporary download staging). Core default `agent-ignore` uses `spawn/**` with navigation/rules exceptions (covers temp staging under `.metadata/temp/`). |
| **Meaning** | Bootstrap target repo so extensions, IDEs, and navigation have a defined home; hide utility-only and staging paths from agents. |

---

## 4. `add-ide-to-list(ide)` / `remove-ide-from-list(ide)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Current `spawn/.metadata/ide.yaml`. |
| **How** | Parse YAML; append unique IDE name or remove name; preserve order semantics defined in `data-structure.md`. |
| **Writes** | Updated `spawn/.metadata/ide.yaml`. |
| **Meaning** | Record which IDEs participate in refresh/uninstall without implied rendering (orchestrators call adapters separately). |

---

## 5. `list-extensions()` / `list-ides()`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.extend/*/` directory names; `spawn/.metadata/ide.yaml` `ides` list. |
| **How** | Filesystem listing; YAML parse. |
| **Writes** | None. |
| **Meaning** | Enumerate installed extension packages and initialized IDE adapters for higher-level loops. |

---

## 6. Read helpers: `global` / `local` / `folders` / `removable`

### `get-required-read-global(extension)` / `get-auto-read-global(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.extend/{extension}/config.yaml` — `files` entries with `globalRead: required` or `globalRead: auto`. |
| **How** | Config parse; collect path + description per declared rule. |
| **Writes** | None. |
| **Meaning** | Inputs for **navigation** (`read-required` / `read-contextual` at repo level) and for **skill metadata** merging (global file sets). |

### `get-required-read-global()` / `get-auto-read-global()`

| Aspect | Detail |
| --- | --- |
| **Reads** | Every installed extension via `list-extensions()`. |
| **How** | For each extension, call the single-extension variant; return **dict[extension_id, flat list]**. |
| **Writes** | None. |
| **Meaning** | Whole-repo view for navigation generation. Do **not** return a single flat merged list from this entry point. |

### `get-required-read-ext-local(extension)` / `get-auto-read-local(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Same `config.yaml` — `localRead` flags on `files`. |
| **How** | Config parse. |
| **Writes** | None. |
| **Meaning** | Files that must appear in **rendered skills** for this extension (mandatory vs contextual auto-read), combined with per-skill overrides in `generate-skills-metadata`. |

### `get-folders(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `config.yaml` `folders` map. |
| **How** | Config parse. |
| **Writes** | None. |
| **Meaning** | Declared directory artifacts for install/materialization and collision checks. |

### `get-removable(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `config.yaml` `files` / `folders` with **static** disposition (not artifact). |
| **How** | Filter by mode; exclude artifacts from default uninstall removal. |
| **Writes** | None. |
| **Meaning** | Uninstall deletes these target paths after rendered IDE state is cleared; artifacts remain unless scripts migrate. |

---

## 7. Skills: discovery, raw info, normalized metadata

### `list-skills(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.extend/{extension}/skills/*.md` (filesystem). |
| **How** | Enumerate skill source paths under installed extension. |
| **Writes** | None. |
| **Meaning** | Source list before metadata generation; agents do not read these paths directly in normal flow (see `agentic-flow.md`). |

### `get-skill-raw-info(extension, skillPath)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Skill file contents; optional overrides from `config.yaml` `skills` entry keyed by filename; optional YAML frontmatter in skill. |
| **How** | Parse Markdown: strip optional notation/frontmatter; resolve `name`, `description`, `required-read` list and body `content`. |
| **Writes** | None. |
| **Meaning** | One skill’s **authoring-time** view before merging with global/local read rules. |

### `generate-skills-metadata(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `list-skills` + per-skill `get-skill-raw-info`; **`get-required-read-global()`** (no extension arg — **dict** keyed by extension; **flatten** all values to build the “all global required” file set across the repo); **`get-auto-read-global()`** same for auto; **`get-required-read-ext-local(extension)`** and **`get-auto-read-local(extension)`** (**flat** lists for the current extension only). |
| **How** | `required-read = distinct(skill.required-read ∪ local_required ∪ flattened_global_required)`; `auto-read = distinct(local_auto ∪ flattened_global_auto)`; first-seen description wins on duplicates (`2-core-low-level.md` notes). |
| **Writes** | None (pure transform). |
| **Meaning** | Produce **normalized `SkillMetadata[]`** for all IDE `add_skills` adapters — single contract across Cursor, Codex, etc. |

---

## 8. MCP: `list-mcp(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.extend/{extension}/mcp.json`. |
| **How** | Parse JSON → **NormalizedMcp** (servers, transport, env with `secret` / `source: user`, capabilities). Inject extension identity for ownership. |
| **Writes** | None. |
| **Meaning** | IDE-agnostic MCP graph; adapters map to Cursor `.cursor/mcp.json`, Codex TOML, VS Code `servers`/`inputs`, etc. Secrets are never written as literal values in repo files. |

---

## 9. Navigation: `get-navigation-metadata` / `save-extension-navigation` / `save-rules-navigation`

### `get-navigation-metadata(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Same as global required/auto file sets for one extension (shortcut for navigation builders). |
| **How** | Config-driven extraction. |
| **Writes** | None. |
| **Meaning** | Building block for `spawn/navigation.yaml` extension sections. |

### `save-extension-navigation(extension, readRequiredFiles, readContextualFiles)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Current `spawn/navigation.yaml` (round-trip YAML). |
| **How** | Replace or remove the **extension-keyed** section; empty lists remove the section. |
| **Writes** | `spawn/navigation.yaml`. |
| **Meaning** | Publish **read-required** / **read-contextual** index for agents; see `agentic-flow.md`. |

### `save-rules-navigation()`

| Aspect | Detail |
| --- | --- |
| **Reads** | Filesystem `spawn/rules/`; current `spawn/navigation.yaml`. |
| **How** | New rule files → default add to `read-required` → `rules` group; entries pointing at missing files → remove entry + **warning**. |
| **Writes** | `spawn/navigation.yaml`. |
| **Meaning** | Keep target-local rules discoverable without hand-editing navigation for every new file. |

### `refresh-rules-navigation()` (high-level alias for CLI)

| Aspect | Detail |
| --- | --- |
| **Reads** / **Writes** | Same as `save-rules-navigation()` — single call-through. |
| **How** | Invoked by `spawn rules refresh`; acquires lock at CLI layer. |
| **Meaning** | Lets users and CI resync rules after adding/removing files under `spawn/rules/` without a full extension or navigation rebuild. |

---

## 10. Agent ignore: core + extensions + IDE merge

### `get-core-agent-ignore()`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.core/config.yaml` `agent-ignore` list. |
| **How** | YAML parse. |
| **Writes** | None. |
| **Meaning** | Repo-wide globs (e.g. `spawn/**`) merged into IDE ignore surfaces. |

### `get-ext-agent-ignore(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `config.yaml` `agent-ignore`. |
| **How** | YAML parse. |
| **Writes** | None. |
| **Meaning** | Per-extension globs (e.g. hide `spawn/.extend/**` from agents). |

### `get-all-agent-ignore()`

| Aspect | Detail |
| --- | --- |
| **Reads** | `get-core-agent-ignore()` plus every `get-ext-agent-ignore(e)` for `e in list-extensions()`. |
| **How** | Concatenate / dedupe per implementation policy. |
| **Writes** | None. |
| **Meaning** | Single set passed to `refresh-agent-ignore` for a given IDE. |

### `get-agent-ignore-list(ide)` / `save-agent-ignore-list(ide, items)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.metadata/{ide}/agent-ignore.txt`. |
| **How** | Text I/O; replace file with merged list spawn last wrote for that IDE. |
| **Writes** | `agent-ignore.txt`. |
| **Meaning** | **Ownership record** for which globs Spawn injected into IDE-specific ignore (`.cursorignore`, permissions JSON, etc.). |

---

## 11. Gitignore: extension decls vs repo file

### `get-ext-git-ignore(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `config.yaml` `git-ignore`. |
| **How** | YAML parse. |
| **Writes** | None. |
| **Meaning** | Extension-authored globs that should appear in root `.gitignore`. |

### `get-git-ignore-list()` / `save-git-ignore-list(items)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.metadata/git-ignore.txt`. |
| **How** | Text I/O; file is authoritative merged list of Spawn-owned gitignore lines. |
| **Writes** | `git-ignore.txt`. |
| **Meaning** | Track what Spawn added so `refresh-gitignore` can diff push/remove against root `.gitignore`. |

### `get-global-gitignore()` / `push-to-global-gitignore(items)` / `remove-from-global-gitignore(items)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Repository root `.gitignore`. |
| **How** | Parse or line-oriented merge; preserve **non-Spawn** lines; use managed block or ownership list (`utility.md` / `2-core-low-level.md`). |
| **Writes** | Root `.gitignore`. |
| **Meaning** | Materialize extension `git-ignore` + core patterns (e.g. `spawn/.metadata/temp/`) without clobbering user ignores. |

---

## 12. Rendered skills / MCP metadata (Spawn ownership)

### `get-rendered-skills(ide, extension)` / `save-skills-rendered(ide, extension, skillPaths)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.metadata/{ide}/rendered-skills.yaml`. |
| **How** | YAML parse; rewrite one `extensions.{ext}` section with list of `{skill, path}` pointing at **rendered** files in repo (e.g. `.agents/skills/.../SKILL.md`); empty → remove section. |
| **Writes** | `rendered-skills.yaml`. |
| **Meaning** | Uninstall/refresh can delete **only** Spawn-written skill files; see `data-structure.md`. |

### `get-rendered-mcp(ide, extension)` / `save-mcp-rendered(ide, extension, mcpNames)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.metadata/{ide}/rendered-mcp.yaml`. |
| **How** | YAML parse; rewrite `extensions.{ext}` server **names** (IDE config keys); empty → remove section. |
| **Writes** | `rendered-mcp.yaml`. |
| **Meaning** | Uninstall/refresh removes correct MCP server blocks from merged IDE configs. |

**Note:** Adapters return paths/names to the orchestrator; **adapters must not**
write these YAML files themselves (`ide-adapters.md` Ownership Records).

---

## 13. IDE adapter surface (coordination layer)

Logical names in `utility.md` map to `IdeAdapter` methods (`ide-adapters.md`):

| Adapter call | **Reads (inputs)** | **Writes (typical)** | **Meaning** |
| --- | --- | --- | --- |
| `add_skills(targetRoot, skillMetadata[])` | Normalized metadata from `generate-skills-metadata` | IDE skill files / rules | Materialize agent-facing procedures per IDE. |
| `remove_skills(targetRoot, renderedPaths[])` | Records from `get-rendered-skills` | Deletes those paths only | Tear down prior render before rebuild or uninstall. |
| `add_mcp(targetRoot, normalizedMcp)` | From `list-mcp` merge (per extension) | IDE MCP config | Add/update server stanzas with placeholders for secrets. |
| `remove_mcp(targetRoot, renderedMcpNames[])` | From `get-rendered-mcp` | MCP config | Remove Spawn-owned servers by name. |
| `add_agent_ignore(targetRoot, globs[])` | Merged glob list from `get-all-agent-ignore` | IDE ignore file or settings | **`void` / `None` only** — Spawn tracks ownership in `agent-ignore.txt`, not via a return value. |
| `remove_agent_ignore(targetRoot, globs[])` | Subset from saved agent-ignore list | IDE ignore file | Revert Spawn-owned globs on `remove-ide` / uninstall. |
| `rewrite_entry_point(targetRoot, prompt)` | Fixed prompt from high-level constant | `AGENTS.md`, `CLAUDE.md`, etc. | Inject **managed block** with navigation contract. |
| `detect(targetRoot)` | Repo footprint | None | Capability and “used” heuristics. |

Unsupported operations: **warn**, leave corresponding metadata unchanged for that
operation.

---

## 14. Extension setup scripts

| Function | **Reads** | **How** | **Writes** | **Meaning** |
| --- | --- | --- | --- | --- |
| `run-before-install-scripts(extension)` | `config.yaml` setup; scripts under `spawn/.extend/{ext}/setup/` | `subprocess`, `cwd = target_root`, env `SPAWN_*` | None (unless script mutates repo intentionally) | **Blocking** on failure before copy/refresh. |
| `run-after-install-scripts(extension)` | Same | Same | — | **Warning** on failure after state refreshed. |
| `run-before-uninstall-scripts(extension)` | Same | Same | — | If **not configured**, skip. If configured, **must** run; failure is **blocking** (`SpawnError`). |
| `run-after-uninstall-scripts(extension)` | Same | Same | — | Warning on failure. |
| `run-healthcheck-scripts(extension)` | Same | Same | None | Non-mutating validation signal for CI/human. |

---

## 15. High-level: `refresh-gitignore`

| Step | Calls / data | Persistence |
| --- | --- | --- |
| 1 | `new = ∪_e get-ext-git-ignore(e)` (all installed extensions) | — |
| 2 | `existing = get-git-ignore-list()` | — |
| 3 | `save-git-ignore-list(new)` | `git-ignore.txt` |
| 4 | `push-to-global-gitignore(new \ existing)` | root `.gitignore` |
| 5 | `remove-from-global-gitignore(existing \ new)` | root `.gitignore` |

**Semantics:** Converge root `.gitignore` with union of extension-declared patterns
Spawn owns; **idempotent** replays.

---

## 16. High-level: `refresh-agent-ignore(ide)`

| Step | Calls / data | Persistence |
| --- | --- | --- |
| 1 | `old = get-agent-ignore-list(ide)` (Spawn-owned globs last written for this IDE) | — |
| 2 | `new = merged deduplicated list from get-all-agent-ignore()` | — |
| 3 | `remove_agent_ignore(targetRoot, old \ new)` — drop globs no longer required | IDE-specific file / settings |
| 4 | `add_agent_ignore(targetRoot, new \ old)` — add newly required globs | IDE-specific file / settings |
| 5 | `save-agent-ignore-list(ide, new)` | `agent-ignore.txt` |

Equivalent **full-replace** strategy is acceptable if the adapter applies a single managed block: `remove_agent_ignore(targetRoot, old)` then `add_agent_ignore(targetRoot, new)`, then step 5 — as long as only Spawn-owned entries are touched (`ide-adapters.md`).

**Semantics:** Same **diff** pattern as `refresh-gitignore` (`utility.md` Rebuild Semantics: ignore rebuilds compare metadata lists and apply only Spawn-owned additions/removals). Prevents stale globs after extension uninstall or config shrink.

---

## 17. High-level: `refresh-skills(ide, extension)`

| Step | Calls / data | Persistence |
| --- | --- | --- |
| 1 | `old = get-rendered-skills(ide, extension)` | — |
| 2 | `meta = generate-skills-metadata(extension)` | — |
| 3 | **Validate** global uniqueness: normalized skill names across **all** installed extensions for this IDE must stay pairwise distinct after this refresh (`utility.md`, Cross-extension rendered identity). | — |
| 4 | `remove_skills(targetRoot, old)` | Deletes old skill files |
| 5 | `paths = add_skills(targetRoot, meta)` | IDE skill paths |
| 6 | `save-skills-rendered(ide, extension, paths)` **only after step 5 succeeds** | `rendered-skills.yaml` |

**Semantics:** Validate-then-remove-then-add; metadata updates **after** successful `add_skills`. If step 5 fails, do not run step 6; **repair** = rerun the same refresh (Core Rules: Refresh ordering and recovery).

---

## 18. High-level: `refresh-mcp(ide, extension)`

| Step | Calls / data | Persistence |
| --- | --- | --- |
| 1 | `old_names = get-rendered-mcp(ide, extension)` | — |
| 2 | `norm = list-mcp(extension)` | — |
| 3 | **Validate** every server name in `norm` against all other extensions' MCP names for this merge target. | — |
| 4 | `remove_mcp(targetRoot, old_names)` | IDE MCP file |
| 5 | `names = add_mcp(targetRoot, norm)` | IDE MCP file |
| 6 | `save-mcp-rendered(ide, extension, names)` **only after step 5 succeeds** | `rendered-mcp.yaml` |

**Semantics:** Same pattern as §17; no metadata persist on failed `add_mcp`.

---

## 19. High-level: `remove-skills` / `remove-mcp` (per IDE + extension)

| Function | Flow | Persistence |
| --- | --- | --- |
| `remove-skills(ide, extension)` | `get-rendered-skills` → `remove_skills` → clear section in `rendered-skills.yaml` | YAML updated |
| `remove-mcp(ide, extension)` | `get-rendered-mcp` → `remove_mcp` → clear section in `rendered-mcp.yaml` | YAML updated |

**Semantics:** Targeted teardown without full refresh (used in uninstall / remove-ide paths).

---

## 20. High-level: `refresh-entry-point(ide)`

| Step | Calls / data | Persistence |
| --- | --- | --- |
| 1 | Build constant prompt: read `spawn/navigation.yaml`, consume all `read-required`, choose `read-contextual` by task | — |
| 2 | `ide.Get(ide).rewrite_entry_point(targetRoot, prompt)` | Entry file with managed `<!-- spawn:start -->` block |

**Semantics:** Ensure every initialized IDE has the same **navigation contract**
without duplicating full rule text (`ide-adapters.md`).

---

## 21. High-level: `refresh-extension(ide, extension)`

| Order | Action |
| --- | --- |
| 1 | `refresh-mcp(ide, extension)` |
| 2 | `refresh-skills(ide, extension)` |
| 3 | `refresh-agent-ignore(ide)` (typically whole-IDE rebuild from merged globs; see orchestrator implementation) |

**Semantics:** One IDE’s view of one extension’s renderables + shared ignore refresh.

---

## 22. High-level: `remove-extension(ide, extension)`

| Order | Action |
| --- | --- |
| 1 | `remove-mcp(ide, extension)` |
| 2 | `remove-skills(ide, extension)` |
| 3 | Remove Spawn-owned agent-ignore entries for `ide` tied to this extension or full IDE list per policy |
| 4 | Clear rendered metadata sections for that extension |

**Semantics:** Strip Spawn outputs for this pair before removing package or IDE.

---

## 23. High-level: `refresh-extension(extension)` (full extension install/update path)

| Order | Phase |
| --- | --- |
| 1 | `run-before-install-scripts(extension)` — **blocking** |
| 2 | For each `ide in list-ides()`: `refresh-extension(ide, extension)` (MCP, skills, agent-ignore as designed) |
| 3 | Materialize static/artifact files from `spawn/.extend/{ext}/files/` per `config.yaml` modes |
| 4 | `refresh-navigation` (rebuild from all extensions + `save-rules-navigation`) |
| 5 | `refresh-gitignore` |
| 6 | For each IDE: `refresh-entry-point(ide)` if full refresh policy requires |
| 7 | `run-after-install-scripts(extension)` — **warning** only on failure |

**Semantics:** After extension source lands under `spawn/.extend/{ext}`, converge
**all** agent surfaces and repo-owned files declared by the extension.

*(Exact ordering of entry-point refresh vs per-extension refresh may match
`3-core-high-level.md`; navigation/gitignore before or after materialization must
respect blocking scripts and collision checks from `lifecycle.md` in utility.)*

---

## 24. High-level: `remove-extension(extension)`

| Order | Phase |
| --- | --- |
| 1 | `run-before-uninstall-scripts` per blocking rules |
| 2 | For each IDE: remove MCP/skills (and agent-ignore contribution) for this extension |
| 3 | Delete static paths from `get-removable(extension)`; **keep** artifacts |
| 4 | Delete `spawn/.extend/{extension}/` tree |
| 5 | `refresh-navigation`, `refresh-gitignore`, `refresh-agent-ignore` per IDE, `refresh-entry-point` as needed |
| 6 | `run-after-uninstall-scripts` |

**Semantics:** Remove methodology package and Spawn-owned target files while
preserving artifacts.

---

## 25. High-level: `update-extension(extension)`

| Aspect | Detail |
| --- | --- |
| **Reads** | `spawn/.extend/{extension}/source.yaml`; remote/local source via download layer; existing artifact paths on disk. |
| **How** | Resolve source → **staging** `spawn/.metadata/temp/{operation_id}/` when needed → validate **newer** version (else error) → replace static tree under `.extend` → run setup scripts → same refresh cascade as install. |
| **Writes** | Updated `.extend`, `source.yaml`, rendered outputs, navigation, ignores. |
| **Meaning** | In-place methodology upgrade without orphan rendered files. |

---

## 26. `download-extension(path, branch)`

| Step | Data | I/O |
| --- | --- | --- |
| 1 | Allocate `operation_id`; stage under `{targetRoot}/spawn/.metadata/temp/{operation_id}/` for git/zip | git clone / httpx + zip extract |
| 2 | Validate staged `extsrc/config.yaml`, collisions, version vs existing `source.yaml` | reads: other extensions’ configs |
| 3 | `shutil.copytree` of `extsrc/` → `spawn/.extend/{extension}/` | write |
| 4 | Write `spawn/.extend/{extension}/source.yaml` with identity | write |
| 5 | `finally`: remove `spawn/.metadata/temp/{operation_id}/` | delete |

**Semantics:** Safe copy **after** validation; **no** partial `.extend` on hard
failures before copy phase.

---

## 27. `install-extension(path, branch)`

| Aspect | Detail |
| --- | --- |
| **Composes** | `download-extension` then `refresh-extension(extension)` (full lifecycle including scripts per `utility.md` ordering). |

---

## 28. `list-extensions(buildPath, branch)` (build manifest)

| Aspect | Detail |
| --- | --- |
| **Reads** | Resolve build repo to staging if remote → read `extensions.yaml` (or build-specific manifest path from `extensions.md`). |
| **How** | Same staging rules as other downloads. |
| **Writes** | None (pure read). |
| **Meaning** | Returns ordered list of `{path, branch}` for `install-build`. |

---

## 29. `install-build(path, branch)`

| Aspect | Detail |
| --- | --- |
| **Reads** | Output of `list-extensions(buildPath, branch)`. |
| **How** | For each entry: `install-extension` or equivalent refresh if already present (per command semantics). |
| **Writes** | Multiple `.extend` dirs + cumulative navigation/ignores/IDE renders. |
| **Meaning** | Batch bootstrap from a **build** repo (preset methodology bundle). |

---

## 30. Authoring commands (minimal I/O)

### `extension_init(path, name)`

| **Reads** | Check existence of `{path}/extsrc/config.yaml`. |
| **Writes** | Create `extsrc/` skeleton: `config.yaml`, empty dirs `skills/`, `files/`, `setup/`. |
| **Meaning** | Greenfield extension authoring **outside** target `spawn/.extend` until `extension add`. |

### `extension_check(path)`

| **Reads** | `extsrc/` tree — config, skills, scripts, `mcp.json`, declared files modes. |
| **Writes** | None. |
| **Meaning** | CI/local validation without mutating a target repo. |

### `extension_from_rules(source, outputPath, name, branch)`

| **Reads** | Resolve `source` → staging when remote; read `spawn/rules/`, `spawn/navigation.yaml` from **resolved** target. |
| **Writes** | `{outputPath}/extsrc/` generated tree + `config.yaml`. |
| **Meaning** | Reverse-methodology: derive packable extension from an existing repo’s rules/navigation. |

### `extension-healthcheck(extension)`

| **Reads** | Installed `spawn/.extend/{ext}/` + `run-healthcheck-scripts`. |
| **Writes** | None from checker (scripts may log). |
| **Meaning** | Operational sanity before/after upgrades. |

---

## 31. IDE lifecycle: `add-ide(ide)` / `remove-ide(ide)`

### `add-ide(ide)`

| Step | Action |
| --- | --- |
| 1 | `add-ide-to-list(ide)` |
| 2 | Init `spawn/.metadata/{ide}/` files if missing |
| 3 | `detect(ide)`; **warn** if `skills` or `mcp` capabilities insufficient for Spawn’s repo-scoped rendering |
| 4 | `refresh-entry-point(ide)` |
| 5 | For each extension: `refresh-mcp`, `refresh-skills`, then `refresh-agent-ignore(ide)` (or combined per `3-core-high-level.md`) |

**Semantics:** Register IDE then project all current methodology onto that surface.

### `remove-ide(ide)`

| Step | Action |
| --- | --- |
| 1 | For each extension: `remove-mcp`, `remove-skills`, strip agent-ignore |
| 2 | `remove-ide-from-list(ide)` |

**Semantics:** Leave extensions installed but remove IDE-specific rendered **artifacts**.

---

## Related documents

- `spec/design/utility.md` — normative command and module names
- `spec/design/data-structure.md` — file shapes and paths
- `spec/design/ide-adapters.md` — adapter matrix and removal semantics
- `spec/design/agentic-flow.md` — how agents consume navigation vs rendered skills
- `spec/tasks/_DONE_2-implementation-detail-designs/_DONE_3-core-high-level.md` — implementation grouping
