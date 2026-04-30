## What is Spawn?

Spawn is a framework for building **AIDD** (AI-driven development) methodologies. It supports both **authoring** methodologies and **applying** them in a project. Within a single repository you can use **several** AIDD methodologies in a coherent way—shared navigation, skills, rules, and tooling stay aligned instead of competing ad hoc setups.

## What is spawn-cli?

**spawn-cli** is the utility that manages methodologies installed in your project. In Spawn terminology those packs are **extensions**: versioned content that usually lives in a **Git** repository. The CLI **instantiates** instruction files, process descriptions, rules, agent skills, and wires their behavior together (navigation, IDE-facing outputs, optional lifecycle hooks). Extensions can also declare **MCP servers**, **agent-ignore** patterns, **git-ignore** entries, and similar integration points—see [`spec/design/extension-author-guide.md`](spec/design/extension-author-guide.md).

### How spawn-cli keeps methodologies coherent

Several methodologies in one repo stay aligned because Spawn maintains **one shared navigation index**: [`spawn/navigation.yaml`](spec/design/data-structure.md) aggregates mandatory and contextual reads from **every installed extension** plus local [`spawn/rules/`](spec/design/user-guide.md) (refreshed with `spawn rules refresh`). Agents are steered through that file instead of chasing disconnected README fragments.

On each install or refresh, the CLI **regenerates IDE-facing artifacts** so skills and entry points stay consistent across extensions: rendered skill bodies include **paths and descriptions** wired from navigation (required reads, contextual hints, rule files), MCP snippets normalize server definitions per IDE adapter, and ignore lists merge without manual copy-paste. The net effect is that methodology files, generated skill links, and repo rules **compose** rather than contradict each other.

**Example:** [**spawn-ext-spectask**](https://github.com/noant/spawn-ext-spectask) (Spec-Tasks methodology: spec layout, skills, design index) and [**spawn-ext-creator**](https://github.com/noant/spawn-ext-creator) (authoring flows, including agent-guided extension bootstrap) can be installed in the **same** repository and still share that single index and merged IDE outputs.

## How to install spawn-cli

**Recommended:** install `spawn` on your `PATH` with **uv**:

```bash
uv tool install spawn-cli && spawn --help
```

Run once without installing (ephemeral **uvx**):

```bash
uvx --from spawn-cli spawn --help
```

**Upgrade** the persistent uv tool:

```bash
uv tool upgrade spawn-cli && spawn --help
```

Force a fresh resolver for a one-shot run:

```bash
uvx --refresh --from spawn-cli spawn --help
```

Additional installers (**pip**, **pipx**, local checkout) and upgrade notes: **[spec/design/user-guide.md](spec/design/user-guide.md#other-installation-options)**.

## How spawn-cli works

Run commands from the **root of the repository** you are configuring. Almost every command requires `spawn init` first (it creates the `spawn/` tree). Only one Spawn process should touch a repo at a time (file lock).

### Initialize a repo

```bash
spawn init
```

### IDE adapters

For each **supported IDE** adapter, show whether it **looks used in the current repository** and what it can render (e.g. skills, MCP, agent-ignore):

```bash
spawn ide list-supported-ides
```

Register or drop IDE keys for **this** repo (examples: `cursor`, `codex`):

```bash
spawn ide add cursor
spawn ide add cursor codex
spawn ide remove codex
spawn ide list
```

### Extensions

Add from a Git URL, optional branch (also supports ZIP paths and local directories/archives):

```bash
spawn extension add https://github.com/noant/spawn-ext-spectask
spawn extension add https://github.com/noant/spawn-ext-spectask --branch main
```

Maintain installed packs:

```bash
spawn extension list
spawn extension update spectask
spawn extension reinstall spectask
spawn extension remove spectask
spawn extension healthcheck spectask
```

Authoring helpers (run inside or next to an extension project):

```bash
spawn extension init ./my-ext --name my-ext
spawn extension check ./my-ext
spawn extension check ./my-ext --strict
spawn extension from-rules ./repo-with-spawn-rules --name my-ext --output ./out
```

### Navigation from repo rules

After editing files under `spawn/rules/`, refresh mandatory reads in `spawn/navigation.yaml`:

```bash
spawn rules refresh
```

### Batch install from a build manifest

`spawn build list` / `spawn build install` take a **build source** (positional argument; there is no implicit default):

- **Local directory** whose root contains **`extensions.yaml`**. Spawn resolves the path (e.g. `.` → current working directory) and reads **`<that-directory>/extensions.yaml`** — not a path to the YAML file itself.
- Otherwise a **Git URL**, **ZIP URL**, or **local path** to a repository tree: Spawn stages it, then looks for **`extensions.yaml`** at that root or, if there is exactly one top-level subdirectory, under that folder (`extensions.yaml not found` if neither applies).

Each manifest entry is an extension source; optional per-entry `branch` overrides the CLI default for that row.

Minimal `extensions.yaml`:

```yaml
extensions:
  - path: https://github.com/org/extension-one.git
    branch: main
  - path: https://github.com/org/extension-two.git
```

Dry-run (prints resolved entries as YAML), then install:

```bash
# Manifest at ./extensions.yaml (cwd is usually your initialized target repo if you keep it there)
spawn build list .
spawn build install .

spawn build install /path/to/methodology-bundle
spawn build install https://github.com/org/team-methodology.git --branch main
```

The **`--branch`** flag applies when the **build source** is Git (clone revision). Entries that omit `branch` fall back to that value.

### Example extension

`[spawn-ext-spectask](https://github.com/noant/spawn-ext-spectask)` is a concrete extension you can install with `spawn extension add` as shown above.

---

- **Python:** 3.10+ (see `pyproject.toml`).
- **Deep dives:** `[spec/design/user-guide.md](spec/design/user-guide.md)` and `[spec/design/utility.md](spec/design/utility.md)`.

## How to create an extension

An extension can be a **full** AIDD methodology, **team** conventions (review rules, codestyle), **scaffolds** for projects that default to AIDD-friendly layouts, **skill-only** bundles, or anything else you can express as declarative files plus optional setup hooks—anything that fits the `extsrc/` layout described in the author guide.

**Bootstrap with the creator extension** (install like any other extension after `spawn init`):

```bash
spawn extension add https://github.com/noant/spawn-ext-creator
```

**Scaffold an empty extension** with the CLI (requires `spawn init` in the repo you run from — same as other subcommands). This lays out `extsrc/` with a starter `config.yaml`, plus empty `skills/`, `files/`, and `setup/`:

```bash
spawn extension init --name my-extension
spawn extension init ./my-extension --name my-extension
```

**Agent-guided scaffold** with **[spawn-ext-creator](https://github.com/noant/spawn-ext-creator)** (install the extension above, then `spawn ide add <ide>` so skills render into your IDE): invoke the **`spawn-ext-bootstrap`** skill so the agent lays out a fuller extension repo than the bare CLI skeleton—for example:

> Use the **spawn-ext-bootstrap** skill to bootstrap a new Spawn extension with stable id `my-extension` under `./my-extension`.

Other creator skills (declaring `config.yaml`, skill sources, MCP, verification, etc.) ship under the same extension; see the rendered skill list after install.

Read **[spec/design/extension-author-guide.md](spec/design/extension-author-guide.md)** for the full model: required `extsrc/config.yaml`, mapping files under `extsrc/files/`, optional `skills/`, `mcp.json`, `agent-ignore`, `setup/` scripts, and how static vs artifact content is updated on `spawn extension update`.

**Minimal mental model:**

- `**extsrc/config.yaml`** — `schema`, `version`, stable `**name`** (install path `spawn/.extend/<name>/`), plus `files`, `skills`, ignores, etc.
- `**extsrc/files/**` — template tree mirrored into the target repo according to `files:` entries.
- `**spawn extension check . --strict**` — validate before publishing or tagging a release.

## How to add rules without creating an extension

Project-local conventions can live under **`spawn/rules/`** without packaging them as an extension. After **`spawn init`**, add any files there (for example `spawn/rules/team.md`); Spawn discovers **every file** under that directory tree.

Wire those paths into **`spawn/navigation.yaml`** so mandatory reads stay aligned with what is on disk:

```bash
spawn rules refresh
```

That rescans **`spawn/rules/`**, attaches missing rule files under a **`rules`** group inside **`read-required`** (default description **`Local rule file.`** until you edit it), and drops stale entries whose files were deleted (you may see a warning).

Rule files can be **mandatory** (**`read-required`**) or **contextual** (**`read-contextual`**). **`spawn rules refresh`** only auto-adds **new** paths into **`read-required` → `rules`**. To keep a rule **contextual**, declare it under **`read-contextual` → `rules`** in **`spawn/navigation.yaml`** with the same shape (`path`, `description`)—once a path appears in either rules list, refresh will not duplicate it into the other tier. You can move entries between **`read-required`** and **`read-contextual`** by editing **`spawn/navigation.yaml`**, then run **`spawn rules refresh`** so both lists stay consistent with files on disk.

Extension-backed reads (`ext:` entries) are unrelated—you only maintain **`spawn/rules/**`** plus **`spawn rules refresh`** for repo-local rules.

## License

MIT — see [LICENSE](LICENSE).
