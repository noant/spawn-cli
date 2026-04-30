# spawn-cli

Installable CLI **`spawn`** for initializing and managing Spawn metadata (extensions, IDE adapters, navigation) in a repository.

## Quick start (uv)

Install `spawn` on your `PATH` (persistent **uv** tool environment):

```bash
uv tool install spawn-cli && spawn --help
```

Run once without installing a tool (ephemeral **uvx**):

```bash
uvx --from spawn-cli spawn --help
```

## Upgrade (uv)

Upgrade the persistent tool:

```bash
uv tool upgrade spawn-cli && spawn --help
```

Latest resolver result for a one-shot run:

```bash
uvx --refresh --from spawn-cli spawn --help
```

---

- **Python:** 3.10+ (see `pyproject.toml`).
- **Usage:** run from the **root of the repository** you configure; most commands need `spawn init` first.

## Install

The PyPI package name is **`spawn-cli`**; the console script is **`spawn`**.

### From PyPI

```bash
pip install spawn-cli
spawn --help
```

Isolated install:

```bash
pipx install spawn-cli
spawn --help
```

With **uv** (tool on `PATH`):

```bash
uv tool install spawn-cli
spawn --help
```

One-shot without installing into an environment:

```bash
uvx --from spawn-cli spawn --help
```

### From a local checkout

```bash
cd /path/to/spawn-cli
uv sync
uv run spawn --help
```

Or editable install with **pip**:

```bash
cd /path/to/spawn-cli
pip install -e .
spawn --help
```

## Upgrade

Use the same installer you used for the initial install. **If you use uv only, see [Upgrade (uv)](#upgrade-uv) at the top.**

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

**Local checkout:** pull changes, then reinstall so the editable install sees updates:

```bash
cd /path/to/spawn-cli
git pull
uv sync
# or: pip install -e .
```

## More

Design and command details: `spec/design/user-guide.md` and `spec/design/utility.md`.
