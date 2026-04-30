# Spawn CLI — short user guide

How to install and run the **`spawn`** command against a target repository. Full command semantics are in [`utility.md`](utility.md) (**Public Commands**).

## Requirements

- **Python** 3.11+ (see `pyproject.toml`).
- Run commands from the **root of the repository** you are configuring: the CLI **does not** take `--target`; it uses the **current working directory** (see `utility.md`, Core Rules).
- Except **`spawn init`**, a **`spawn/`** directory must already exist (otherwise **`SpawnError`** whose message includes **`need init before`**).
- Only one Spawn process may use a repository at a time: if the lock is held, you get **`SpawnError`** whose message includes **`Операция в процессе (файл lock detected)`**.

## How to run `spawn`

The PyPI distribution name is **`spawn-cli`**. In `pyproject.toml`, the console script is **`spawn`** → `spawn_cli.cli:main`.

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

**One-shot without installing** (`uvx`): the executable is named `spawn`, not `spawn-cli`, so pin the package:

```bash
uvx --from spawn-cli spawn --help
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

## Typical workflow

1. `cd` to your project root.
2. `spawn init`
3. Then e.g. `spawn ide add cursor`, `spawn extension add ...`, `spawn build install ...` (full list: `utility.md` → **Public Commands**).

Chain commands in order (e.g. `spawn init`, then `spawn build install "<path>"`).

## Subcommand overview

The tree matches `spec/tasks/_DONE_2-implementation-detail-designs/_DONE_5-cli-wiring.md`:

- `spawn init`
- `spawn rules refresh`
- `spawn ide` — `add`, `remove`, `list`, `list-supported-ides`
- `spawn extension` — `add`, `update`, `remove`, `list`, `init`, `check`, `from-rules`, `healthcheck`
- `spawn build` — `install`, `list`

Arguments, behavior, and error handling: **`utility.md`**.
