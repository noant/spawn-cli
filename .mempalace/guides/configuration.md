# MemPalace configuration (reference)

Source of truth for behavior and fields: [Configuration | MemPalace](https://mempalaceofficial.com/guide/configuration.html).

This extension merges **`MEMPALACE_PALACE_PATH=.mempalace/palace`** for both MCP servers so the IDE and **`after_install`** use a **repo-local** Chroma dir by default (resolved against the MCP **cwd**, usually repo root).

Pre-set **`MEMPALACE_PALACE_PATH`** in your environment overrides that. **`MEMPALACE_EXTENSION_GLOBAL_PALACE=1`** during **`spawn extension add/update`** only affects **`after_install`** (it skips forcing repo-local **`MEMPALACE_PALACE_PATH`** for **`mempalace init`**); MCP still merges the **`env`** stanza unless you edit the IDE’s merged MCP config for a genuinely global **`mempalace-mcp`**.

## Global config

File: `~/.mempalace/config.json`.

Prefer a single canonical style for **`palace_path`** on Windows (either all `\` escapes in JSON such as `C:\\Users\\...\\palace` or a normalized forward-slash path); mixed separators are easy to accumulate when editing by hand.

| Key | Default | Purpose |
|-----|---------|---------|
| `palace_path` | `~/.mempalace/palace` | ChromaDB / palace data directory |
| `collection_name` | `mempalace_drawers` | ChromaDB collection name |
| `people_map` | `{}` | Entity name variants → canonical names |

For additional keys and behavior, see the installed package on [PyPI](https://pypi.org/project/mempalace/) and the upstream repository.

## Project files after `mempalace init`

Created in the project directory, including:

- **`mempalace.yaml`** — wing, rooms, and optionally `palace_path`.
- **`entities.json`** — people / entity map for the project.

The `.mempalace/` tree (metadata, vector store, wings) is created during init; exact layout depends on your CLI version — use `mempalace init --help`.

### `mempalace.yaml` shape (do not guess)

Use only keys your installed CLI documents; the [official configuration page](https://mempalaceofficial.com/guide/configuration.html) shows this core surface:

| Key | Role |
|-----|------|
| `wing` | Single project wing label (string). |
| `rooms` | List of **room names** (palace labels / loci). These are **not** filesystem paths in the YAML — see [Rooms vs repo paths](#rooms-vs-repo-paths-for-agents) below. |
| `palace_path` | Optional override for this project’s Chroma root (often omitted when using **`MEMPALACE_PALACE_PATH`** / global `config.json`). |

Wings can also come from **directory names**, detected **people**, or **`--wing`** on **`mine`** — see upstream docs. Treat the samples below as **patterns to copy and rename**, not exhaustive API.

### Rooms vs repo paths (for agents)

MemPalace ties **content** to the palace through **what directory you mine**, not through a `path:` field per room in `mempalace.yaml` (official examples use **plain strings** only). Use this mental model:

1. **`rooms:`** — short, stable **labels** you want in the palace (often mirroring important top-level folders or slices you care about). They should match how you talk about the codebase (“backend”, `packages_api`, `internal_worker`).
2. **Filesystem coverage** — pass a **directory** to **`mempalace mine`**: repo root **`.`** for the whole tree, or a **relative path** (from the repo root) for one subtree, e.g. `src`, `packages/api`, `apps/web`.
3. **`wing`** — must line up with **`mempalace.yaml`** and with **`--wing` / MCP `wing`** when you mine a slice so indexing stays consistent.

**Mapping labels to folders (examples):** pick a convention and keep it consistent — many teams use the **folder’s basename** as the room name when one folder = one room, or **flatten** nested paths with underscores when one room spans a path.

| `rooms:` entry (label) | Typical folder to mine (relative to repo root) | Notes |
|------------------------|--------------------------------------------------|--------|
| `src` | `src` | one room = one directory |
| `cmd` | `cmd` | matches [minimal](#illustrative-mempalaceyaml-examples) / Go-style trees |
| `web` | `apps/web` | label is short; **mine** the real path |
| `pkg_api` | `packages/api` | nested path → mnemonic label (underscores) |
| `internal_auth` | `internal/auth` | same idea for deep trees |

**CLI (from repo root):** mine the whole project after editing `mempalace.yaml`:

```bash
mempalace mine . --wing myproject
```

Mine only one subtree (same palace, scoped directory):

```bash
mempalace mine packages/api --wing myproject
```

**MCP (`mempalace_mine`):** the bridge only accepts **`directory`**, **`mode`**, **`wing`**, **`palace`**. Use **`directory`** for the path — typically `"."` for full repo or a relative path like `"packages/api"` (workspace cwd is usually repo root):

```json
{
  "directory": "packages/api",
  "wing": "myproject",
  "mode": "projects",
  "palace": null
}
```

After you **add, rename, merge, or split** logical rooms in **`mempalace.yaml`**, plan a **fresh `mine`** for the affected trees so the palace matches the new layout.

If a future MemPalace CLI version documents **structured objects** under `rooms:` (e.g. per-room path keys), prefer **that** schema over the string-only patterns here.

### Illustrative `mempalace.yaml` examples

**1. Minimal (matches upstream tutorial)** — small project, default global palace:

```yaml
wing: myproject
rooms:
  - backend
  - frontend
  - decisions
```

**2. Repo-local palace (aligned with this extension)** — Chroma under the repo regardless of global `palace_path`:

```yaml
wing: acme-service
rooms:
  - cmd
  - internal
  - pkg
  - docs
palace_path: .mempalace/palace
```

On Windows you may use a normalized path; JSON in `~/.mempalace/config.json` still needs valid escaping if you duplicate `palace_path` there.

**3. Full-stack web app** — layer-style rooms without inventing extra YAML keys:

```yaml
wing: coolapp
rooms:
  - api
  - web
  - workers
  - shared
  - db_migrations
  - e2e
palace_path: .mempalace/palace
```

**4. Monorepo / packages** — one wing, many package-shaped rooms:

```yaml
wing: company-platform
rooms:
  - packages_api
  - packages_ui
  - packages_shared
  - apps_admin
  - apps_mobile
  - tooling
  - ci
palace_path: .mempalace/palace
```

**5. Data / ML / notebooks** — pipelines and experiments as rooms:

```yaml
wing: research-bot
rooms:
  - src
  - notebooks
  - data_contracts
  - evals
  - infra
palace_path: .mempalace/palace
```

**6. Docs-heavy or inner-source** — guidance and policies first-class:

```yaml
wing: handbook
rooms:
  - docs
  - runbooks
  - adr
  - examples
  - code
palace_path: .mempalace/palace
```

Room strings should stay short, stable, and ASCII-friendly so MCP logs and **`mempalace_mine --wing`** stay readable. After changing wings or rooms, plan a fresh **`mine`** for affected areas.

### Example `entities.json`

Same shape as global `people_map` — project-level overrides from **`mempalace init`**:

```json
{
  "Kai": "KAI",
  "Priya": "PRI"
}
```

## Identity (layer 0)

File `~/.mempalace/identity.txt` — assistant identity text loaded on wake-up. Write in first person from the assistant’s perspective; see the official configuration guide.

## Overriding palace path

- CLI: `--palace <path>` on commands (`search`, `mine`, etc.).
- MCP: `python -m mempalace.mcp_server --palace <path>` when invoking the module directly.
- Environment: **`MEMPALACE_PALACE_PATH`** (same meaning as `--palace`).
- **`MEMPAL_DIR`** — directory for auto-mining in hooks (see the official env table).

For a **repo-local** palace, set `palace_path` or **`MEMPALACE_PALACE_PATH`** to a directory inside the project (e.g. `<repo>/.mempalace/palace`) consistently for both CLI and MCP.
