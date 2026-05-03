# Spawn CLI — short user guide

How to install and run the **`spawn`** command against a target repository. Command reference: **Commands and options** below; lifecycle, validation, and recovery: [`utility.md`](utility.md).

## Requirements

- **Python** 3.10+ (see `pyproject.toml`).
- Run commands from the **root of the repository** you are configuring: the CLI **does not** take `--target`; it uses the **current working directory** (see `utility.md`, Core Rules).
- Except **`spawn init`**, a **`spawn/`** directory must already exist (otherwise **`SpawnError`** whose message includes **`need init before`**).
- Only one Spawn process may use a repository at a time: if the lock is held, you get **`SpawnError`** whose message includes **`Another Spawn operation is in progress (repository lock held)`**.

## Installation options

The PyPI distribution name is **`spawn-cli`**; the console script is **`spawn`** → `spawn_cli.cli:main` in `pyproject.toml`.

### From PyPI (`pip`, `pipx`)

```bash
pip install spawn-cli
spawn --help
```

Optional isolated install:

```bash
pipx install spawn-cli
spawn --help
```

### With `uv` (persistent tool / one-shot)

**On PATH** (similar to `pipx install`):

```bash
uv tool install spawn-cli
spawn --help
```

**Upgrade** the persistent tool:

```bash
uv tool upgrade spawn-cli && spawn --help
```

**One-shot without installing** (`uvx`): the executable is named `spawn`, not `spawn-cli`, so pin the package:

```bash
uvx --from spawn-cli spawn --help
```

Force a fresh resolver for a one-shot run:

```bash
uvx --refresh --from spawn-cli spawn --help
```

Anywhere you would type `spawn`, you can use `uvx --from spawn-cli spawn` instead if you are not installing into an environment.

### From a local `spawn-cli` checkout

Clone the repo and install from the project root (where `pyproject.toml` lives):

**With `uv`:**

```bash
cd /path/to/spawn-cli
uv sync
uv run spawn --help
```

**With `pip`:**

```bash
cd /path/to/spawn-cli
pip install -e .
spawn --help
```

After `pip install -e .` or `uv tool install` from a local path (e.g. `uv tool install --editable .`), **`spawn`** is on `PATH` like a PyPI install.

### Upgrade (`pip` / `pipx` / local checkout)

Use the same installer you used initially. If you use **uv** only, see **With `uv`** above.

**pip** (current environment):

```bash
pip install --upgrade spawn-cli
spawn --help
```

**pipx**:

```bash
pipx upgrade spawn-cli
spawn --help
```

**Local checkout:** pull changes, then reinstall so an editable install picks up updates:

```bash
cd /path/to/spawn-cli
git pull
uv sync
# or: pip install -e .
```

## Typical workflow

1. `cd` to your project root.
2. `spawn init`
3. Then e.g. `spawn ide add cursor`, `spawn extension add ...`, `spawn build install ...` (all commands: **Commands and options** below; deeper semantics: `utility.md`).

Chain commands in order (e.g. `spawn init`, then `spawn build install "<path>"`).

## Editing `spawn/navigation.yaml`

Maintainers may **hand-edit** **`rules`** groups: paths, **`description`**, and an optional **`hint`** on rows under **`read-required`** only (hints on **`read-contextual` → `rules`** are not consumed into skills or the AGENTS hint rollup). Do **not** manually maintain **`ext`** stanzas (YAML list entries with **`ext:`** and **`files`**, and mirrored **`hints`**): Spawn **overwrites** those blocks when navigation is refreshed. Prefer changing extension-owned text in **`extsrc/config.yaml`** (`hints.global` / `hints.local`) and re-running refresh.

## Commands and options

The CLI is built with nested `argparse` subcommands. Unless noted, every command after **`spawn init`** requires an initialized repo, runs under the **Spawn lock**, and uses **`Path.cwd()`** as the target root (see **Requirements**). Deeper semantics (validation order, recovery): [`utility.md`](utility.md).

### Top level

| Option | Meaning |
| --- | --- |
| `--help` | Standard argparse help for `spawn` or a subcommand. |
| `--version` | Print `spawn <version>` and exit 0. |

---

### `spawn init`

No arguments. Creates the **`spawn/`** tree (config, metadata layout, navigation stub) and ensures temp staging is gitignored. Does not require a prior **`spawn/`**. Acquires the lock while initializing.

---

### `spawn rules refresh`

No additional arguments. Rescans **`spawn/rules/`** and rewrites the **rules** entries in **`spawn/navigation.yaml`** (mandatory reads). Does not reinstall extensions, refresh IDE skills, or rewrite entry points.

---

### `spawn ide`

#### `spawn ide add IDE [IDE ...]`

One or more IDE keys (e.g. `cursor`, `codex`). For each key, registers the IDE and refreshes Spawn-rendered metadata for that adapter.

#### `spawn ide remove IDE [IDE ...]`

Unregisters each IDE: removes Spawn-rendered outputs where the adapter defines cleanup, then drops the key from **`spawn/.metadata/ide.yaml`**.

#### `spawn ide list`

Prints one registered IDE identifier per line to stdout.

#### `spawn ide list-supported-ides`

No extra arguments. Probes the **local machine** for installed IDE tooling, intersected with repo state, and prints **YAML** to stdout. For each canonical IDE key (in **`supported_ide_keys()`** order), the value is a mapping with **`used-in-repo`** and **`capabilities`** (same shape as in **Public Commands** in `utility.md`). Intended for scripts and tooling.

---

### `spawn extension`

#### `spawn extension add SOURCE [--branch REV]`

**`SOURCE`**: local directory or archive, Git URL, or zip URL. Stages the source, validates the extension, runs install lifecycle (materialize files, refresh navigation/skills/MCP/ignores/entrypoints, scripts). **`--branch`**: Git revision when the source is Git; ignored otherwise.

#### `spawn extension update NAME`

**`NAME`**: installed extension id (**`spawn/.extend/<NAME>/`**). Re-fetches from the recorded **`source.yaml`**, requires matching source identity, and refuses to downgrade unless implementation allows **`force`** (user CLI does not expose **`force`**). On success, refreshes the extension like a newer install.

#### `spawn extension reinstall NAME`

**`NAME`**: installed extension id. Recovery path: verifies **`source.yaml`**, **removes** the extension (full uninstall semantics), then **adds** again from the same stored path/branch. Use when the tree is corrupted or you need a clean reinstall without changing the source.

#### `spawn extension remove NAME`

Uninstalls the extension: scripts, rendered MCP/skills, Spawn-owned static paths, then removes **`spawn/.extend/<NAME>/`**. Preserves artifact material per design; see **`utility.md`** (Lifecycle Semantics).

#### `spawn extension list`

Prints one installed extension name per line.

#### `spawn extension init [PATH] --name ID`

**`PATH`**: directory that will contain the scaffold (default **`.`**). **`--name`** (required): canonical extension id. Creates **`extsrc/`** skeleton (**`config.yaml`**, **`skills/`**, **`files/`**, **`setup/`**) if **`extsrc/config.yaml`** does not already exist; if it exists, leaves it unchanged and warns.

#### `spawn extension check [PATH] [--strict]`

**`PATH`**: extension project root (default **`.`**). Resolves **`extsrc/`** or extension root with **`config.yaml`**, validates config, and checks skills, file descriptions, **`extsrc/mcp/*.json`**, etc. **Default**: non-fatal issues become **warnings** printed to stdout (`Warning: ...`); exit **0**. **`--strict`**: issues that are warnings by default become **errors** (**`SpawnError`**), non-zero exit.

#### `spawn extension from-rules SOURCE --name ID [--branch REV] [--output DIR]`

**`SOURCE`**: repo root with **`spawn/rules`**, or remote/Git URL (staged like other sources). **`--name`** (required): extension id for the generated scaffold. **`--branch`**: for Git-backed **`SOURCE`**. **`--output`**: existing directory receiving files (default **`.`**). Produces extension source derived from rules (see `utility.md` / high-level **`extension_from_rules`**).

#### `spawn extension healthcheck NAME`

Runs **`extension_check`** on the installed tree with **strict** semantics, then optional healthcheck setup scripts. Exit **0** if healthy, **1** if validation or scripts fail.

---

### `spawn build`

Commands take a **YAML manifest** path that lists extension sources (see **`install-build`** / **`list-extensions`** in `utility.md`).

#### `spawn build install MANIFEST [--branch REV]`

Resolves the manifest and installs each listed extension serially (same install pipeline as **`extension add`**). **`--branch`**: fallback Git revision when a manifest entry omits an explicit branch.

#### `spawn build list MANIFEST [--branch REV]`

Does not mutate the repo. Resolves the manifest and prints **YAML** of the resolved extension specs to stdout. **`--branch`**: same fallback as **`install`**.

---

For error messages users rely on (**`need init before`**, lock busy, version rules, source identity), see **Core Rules** and **Public Commands** in **`utility.md`**.
