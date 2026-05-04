Wake-up text (~800 tokens):
==================================================
## L0 — IDENTITY
No identity configured. Create ~/.mempalace/identity.txt

## L1 — ESSENTIAL STORY

[mempalace]
  - <!-- spawn:start --> Before working, read `spawn/navigation.yaml`. Read every file listed under `read-required`. Inspect `read-contextual` descriptions and read only files relevant to the current t...  (AGENTS.md)

[spawn]
  - [build-system] requires = ["setuptools>=68"] build-backend = "setuptools.build_meta"  [project] name = "spawn-cli" version = "0.1.15" description = "A minimal installable Python CLI package." readm...  (pyproject.toml)
  - ## What is Spawn?  Spawn is a framework for building **AIDD** (AI-driven development) methodologies. It supports both **authoring** methodologies and **applying** them in a project. Within a single...  (README.md)
  - ogether (navigation, IDE-facing outputs, optional lifecycle hooks). Extensions can also declare **MCP servers**, **agent-ignore** patterns, **git-ignore** entries, and similar integration points—se...  (README.md)
  - es refresh`). Agents are steered through that file instead of chasing disconnected README fragments.  On each install or refresh, the CLI **regenerates IDE-facing artifacts** so skills and entry po...  (README.md)
  - ch other. Optional `hints` add short reminders to rendered skills and the Spawn-managed entry block.  **Example:** [**spawn-ext-spectask**](https://github.com/noant/spawn-ext-spectask) (Spec-Tasks ...  (README.md)
  - emeral **uvx**):  ```bash uvx --from spawn-cli spawn --help ```  **Upgrade** the persistent uv tool:  ```bash uv tool upgrade spawn-cli && spawn --help ```  Force a fresh resolver for a one-shot ru...  (README.md)
  - touch a repo at a time (file lock).  ### Initialize a repo  ```bash spawn init ```  ### IDE adapters  For each **supported IDE** adapter, show whether it **looks used in the current repository** an...  (README.md)
  - tension add https://github.com/noant/spawn-ext-spectask --branch main ```  Maintain installed packs:  ```bash spawn extension list spawn extension update spectask spawn extension reinstall spectask...  (README.md)
  - n `spawn/navigation.yaml`:  ```bash spawn rules refresh ```  ### Batch install from a build manifest  `spawn build list` / `spawn build install` take a **build source** (positional argument; there ...  (README.md)
  - ctly one top-level subdirectory, under that folder (`extensions.yaml not found` if neither applies).  Each manifest entry is an extension source; optional per-entry `branch` overrides the CLI defau...  (README.md)
  - methodology-bundle spawn build install https://github.com/org/team-methodology.git --branch main ```  The **`--branch`** flag applies when the **build source** is Git (clone revision). Entries that...  (README.md)
  - /user-guide.md) and [spec/design/utility.md](spec/design/utility.md).  ## How to create an extension  An extension can be a **full** AIDD methodology, **team** conventions (review rules, codestyle)...  (README.md)
  - ion after `spawn init`):  ```bash spawn extension add https://github.com/noant/spawn-ext-creator ```  **Scaffold an empty extension** with the CLI (requires `spawn init` in the repo you run from — ...  (README.md)
  ... (more in L3 search)
