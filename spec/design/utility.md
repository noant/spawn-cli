# Utility

This document describes how the Spawn CLI transforms a target repository. It is
about command semantics and directory mutations, not parser implementation.

## Core Rules

All paths handled by modules are relative to the target repository root.

The CLI does **not** accept a `--target` flag or equivalent: every command uses
the **current working directory** as the target repository root. Users `cd` into
the repository before running `spawn`.

If `spawn/` is not present (initialization has not been run), every command except
`spawn init` must fail with **`SpawnError`** whose message includes **`need init
before`** (see `spawn init`).

If a file or directory under `spawn/.metadata/` is missing, Spawn creates it on
demand **after** initialization has succeeded.

Spawn removes only entries it owns. Ownership is recorded in:

- `spawn/.metadata/git-ignore.txt`;
- `spawn/.metadata/{ide}/agent-ignore.txt`;
- `spawn/.metadata/{ide}/rendered-skills.yaml`;
- `spawn/.metadata/{ide}/rendered-mcp.yaml`.

Commands should be idempotent whenever they describe a desired repository
state. Re-running `spawn init`, adding an already listed IDE, refreshing an
installed extension, or rebuilding skills should converge to the same rendered
state without duplicating metadata or ignore entries.

### Refresh ordering and recovery (ordering **D**, repair **A**)

Skill and MCP rebuilds follow a fixed phase order:

1. Read prior ownership from `rendered-skills.yaml` / `rendered-mcp.yaml`.
2. Compute the **candidate** rendered state from current extension configs and
   **validate** it (**cross-extension identity**, schema, etc.). If validation
   fails, stop with **`SpawnError`** before mutating IDE files.
3. Call `remove_*` with the recorded prior state (adapter mutates IDE files).
4. Call `add_*` to apply the candidate state.
5. Write ownership metadata **only after** step 4 succeeds and the adapter
   returns the new paths / server names.

If step 4 fails, Spawn **must not** update ownership metadata to describe the
new state; metadata still reflects the pre-step-3 record while IDE files may
already be cleared. The supported fix is **A**: rerun the same refresh (or full
extension / IDE refresh). The next run repeats step 3 (remove is idempotent or
cleans remnants) and retries step 4 until convergence.

**Repository lock:** **Every** CLI command (including read-only diagnostics such
as `spawn ide list-supported-ides` and `spawn extension check`) must acquire the
same repository-local Spawn lock **before** doing any work. Two `spawn`
invocations must never run concurrently against the same repository: there is
**no** waiting or queue. If the lock is already held, fail immediately with
**`SpawnError`** and a user-visible message that includes **`Another Spawn operation is in progress (repository lock held)`**.

Use a **cross-platform** file lock (`filelock` is the baseline dependency) with
**non-blocking** acquisition (for example `timeout=0`) so attempts while another
process holds the lock error out at once on Windows, Linux, and macOS.

**Git** is required **only** for operations that use git remotes (`git clone`,
etc.). If such an operation runs and `git` is not available, fail with
**`SpawnError`** that tells the user to install Git and points to one install
command per OS, for example: **Windows** (`winget install Git.Git`), **macOS**
(`brew install git` or Xcode CLT), **Linux** (`sudo apt install git`,
`sudo dnf install git`, or distro-appropriate).

**Console output:** a single **verbose** policy — everything informative goes to
the console as implemented. There is no log-level flag in the baseline CLI.

Warnings report recoverable inconsistencies such as an IDE without MCP support or a
missing optional setup script. **Duplicate rendered skill or MCP server names
across two installed extensions** are **errors**, not warnings (see Cross-extension
rendered identity).

Errors stop the command before the next mutation when continuing could corrupt
ownership state, overwrite another extension's files, violate global uniqueness
of rendered names, or install an unsupported config schema.

## Cross-extension rendered identity

Rendered **skill** names (after `normalize_skill_name`) and **MCP server** names
(from each extension's `mcp.json`) must be **pairwise distinct across all
installed extensions** in the same target repository for a given refresh
operation. Before calling `add_skills` / `add_mcp`, Spawn validates the union of
names from every extension that contributes to that IDE surface. If two
extensions would render the same skill name or the same MCP server key into the
same IDE merge target, Spawn raises **`SpawnError`** and performs **no** further
mutation in that command (install, update, or refresh).

Authors should prefix generic names with the extension or methodology identifier
(`extensions.md`, Naming). Automatic namespacing or silent overwrite across
extensions is **not** supported.

## Supported IDE keys

The Spawn CLI keeps **one frozen ordered tuple/list constant in source code**
(`spawn_cli.core.low_level.CANONICAL_IDE_KEYS`). That constant is the **only**
authority for canonical key order and membership: **no** environment variables,
**no** user config files, and **no** secondary lists elsewhere. `supported_ide_keys()`
returns that constant verbatim. The registry must register exactly one **concrete**
adapter per key in that list. User-facing aliases (`claude` → `claude-code`, etc.) apply only
when parsing commands; the constant contains canonical identifiers only.

```yaml
# Canonical keys — illustrative order matches Adapter Registry
- cursor
- codex
- claude-code
- windsurf
- github-copilot
- gemini-cli
```

## Low-Level Modules

`supported_ide_keys()` returns the canonical IDE key list above.

`detect_supported_ides(targetRoot)` resolves each key via `ide.Get(key)`, calls
`detect(targetRoot)`, and returns a mapping suitable for YAML serialization:
each canonical IDE key maps to one `DetectResult` (`used-in-repo`,
`capabilities`), as defined in `spec/design/ide-adapters.md`. Intended for
`spawn ide list-supported-ides` and diagnostics.

`init()` creates `spawn/`, `spawn/.core/config.yaml`,
`spawn/.metadata/ide.yaml`, `spawn/.metadata/git-ignore.txt`,
`spawn/rules/`, and `spawn/navigation.yaml` when missing. Core config content
comes from CLI resources (default `agent-ignore` hides `spawn/**` except
navigation and rules; see `data-structure.md`). `init()` also registers
`spawn/.metadata/temp/` in Spawn-managed root `.gitignore` patterns per Temporary download staging.

`add-ide-to-list(ide)` adds an IDE to `spawn/.metadata/ide.yaml`.

`remove-ide-from-list(ide)` removes an IDE from `spawn/.metadata/ide.yaml`.

`list-extensions()` returns folder names under `spawn/.extend/`.

`list-ides()` returns IDE names from `spawn/.metadata/ide.yaml`.

`get-required-read-global(extension)` reads
`spawn/.extend/{extension}/config.yaml` and returns a **flat** list of file
references (path + description) for **that extension only** — entries with
`globalRead: required`.

`get-required-read-global()` (no extension argument) calls the per-extension
function for every installed extension and returns a **map** from extension id →
**flat** list of file references (path + description), not a single flattened
list across all extensions.

`get-required-read-ext-local(extension)` returns files with
`localRead: required` as a **flat** list for that extension.

`get-auto-read-global(extension)` returns a **flat** list — files with
`globalRead: auto` for that extension.

`get-auto-read-global()` returns the same **map** shape as
`get-required-read-global()` but for `globalRead: auto`.

`get-auto-read-local(extension)` returns files with `localRead: auto` as a
**flat** list for that extension.

**Typing rule:** any function whose signature includes `extension` returns only
that extension’s **flat** `list`. Functions that aggregate over all extensions
return **`dict[str, list]`** (or equivalent) keyed by extension id. Every
element includes **both** path and description.

`get-folders(extension)` returns the `folders` section from extension config.

`get-removable(extension)` returns static files and folders from extension
config. Artifact files and folders are not removable by default.

`list-skills(extension)` returns Markdown files from
`spawn/.extend/{extension}/skills/`.

`list-mcp(extension)` parses `spawn/.extend/{extension}/mcp.json` into the
normalized MCP shape described below.

`get-skill-raw-info(extension, skillPath)` returns:

```yaml
name: resolved from config or skill notation
description: resolved from config or skill notation
content: skill content without optional notation block
required-read:
  - spec/main.md
```

`generate-skills-metadata(extension)` merges raw skill info with global and
local read metadata:

- required reads are `distinct(skill.required-read + local required + all
  global required files)`;
- auto reads are `distinct(local auto + all global auto files)`;
- descriptions are resolved from read metadata.

`skill.required-read` is an additive override for files that are mandatory only
for one skill. Extension authors should not list files there when they already
come from `localRead: required` or `globalRead: required`; the generator adds
those categories automatically and de-duplicates the final list.

`get-navigation-metadata(extension)` returns the extension's
`globalRead: required` and `globalRead: auto` file groups.

`get-all-agent-ignore()` returns core and extension agent-ignore globs.

`get-merged-extension-agent-ignore()` returns extension `agent-ignore` globs only,
stable deduped across installed extensions.

`merge-core-and-extension-agent-ignore(core, ext)` returns the usual combined list.

`get-agent-ignore-list(ide)` and `save-agent-ignore-list(ide, items)` read and
replace `spawn/.metadata/{ide}/agent-ignore.txt` (see `data-structure.md` for
native vs project semantics).

`save-skills-rendered(ide, extension, skillPaths)` rewrites the extension
section in `spawn/.metadata/{ide}/rendered-skills.yaml`. If `skillPaths` is
empty, it removes the section.

`get-rendered-skills(ide, extension)` returns rendered skill paths for one
extension from the IDE metadata file.

`save-mcp-rendered(ide, extension, mcpNames)` rewrites the extension section in
`spawn/.metadata/{ide}/rendered-mcp.yaml`. If `mcpNames` is empty, it removes
the section.

`get-rendered-mcp(ide, extension)` returns rendered MCP names for one extension
from the IDE metadata file.

`get-git-ignore-list()` and `save-git-ignore-list(items)` read and replace
`spawn/.metadata/git-ignore.txt`.

`get-global-gitignore()`, `push-to-global-gitignore(items)`, and
`remove-from-global-gitignore(items)` read and mutate the target repository
`.gitignore` while preserving user entries.

`get-ext-git-ignore(extension)` and `get-ext-agent-ignore(extension)` read
ignore sections from extension config.

`get-core-agent-ignore()` reads core ignore globs from
`spawn/.core/config.yaml`.

`save-extension-navigation(extension, readRequiredFiles, readContextualFiles)`
rewrites the extension sections in `spawn/navigation.yaml`. Empty lists remove
the corresponding extension section.

`save-rules-navigation()` syncs navigation with `spawn/rules/`. New rule files
are added to `read-required -> rules`; missing files are removed with a
warning.

`refresh-rules-navigation()` calls `save-rules-navigation()` only. It supports
the `spawn rules refresh` command when authors add or remove files under
`spawn/rules/` and want `spawn/navigation.yaml` updated without running a full
extension refresh or editing YAML by hand.

`list-mcp(extension)` returns data that can be rendered to any IDE:

```yaml
servers:
  - name: spectask-search
    extension: spectask
    transport:
      type: stdio
      command: uvx
      args:
        - spectask-search-mcp
      cwd: .
    env:
      SPECTASK_TOKEN:
        source: user
        required: true
        secret: true
    capabilities:
      tools: true
      resources: false
      prompts: false
```

`transport.type` may be `stdio`, `http`, `sse`, or another supported transport.
Adapters map this structure to IDE-specific MCP config.

Secrets are never materialized into repository-tracked files by Spawn. IDE
adapters may render environment variable names, placeholders, or references to
the IDE's secret mechanism, but the actual value remains user-provided local
configuration.

## IDE-Specific Modules

Each IDE has files with the same logical signatures:

- `ide/{ide}/add-skills.py`
- `ide/{ide}/remove-skills.py`
- `ide/{ide}/add-mcp.py`
- `ide/{ide}/remove-mcp.py`
- `ide/{ide}/add-agent-ignore.py`
- `ide/{ide}/remove-agent-ignore.py`
- `ide/{ide}/rewrite-entry-point.py`
- `ide/{ide}/detect.py`

`add-skills` receives `skill-metadata[]` and writes IDE-specific skills. Global
uniqueness of normalized skill names across installed extensions is validated
**before** this call (`Cross-extension rendered identity`). Overwriting a
destination already listed as Spawn-owned for the **same** extension may emit a
warning; conflicts with non-Spawn files follow `ide-adapters.md` error rules.

`remove-skills` receives rendered skill paths and deletes only those paths.

`add-mcp` and `remove-mcp` add or remove MCP entries. MCP server names are
validated for global uniqueness **before** `add-mcp` (`Cross-extension rendered
identity`). If an IDE does not support MCP, the adapter emits a warning.

`add-agent-ignore` and `remove-agent-ignore` mutate the IDE-specific ignore file
with the given globs (legacy whole-block helpers for single `# spawn:start`
regions; orchestration prefers **`rewrite-core-agent-ignore`** and
**`rewrite-extension-agent-ignore`** on native adapters). **`add-agent-ignore`
returns nothing** (`None`); ownership for native IDEs is tracked via
**`agent-ignore.txt`** for the extension slice and core always follows
`spawn/.core/config.yaml`; project IDEs keep a full-list snapshot in the same
file for JSON diffing.

`rewrite-entry-point(prompt)` writes the IDE-specific entry point file, such as
`AGENTS.md`, `CLAUDE.md`, or another agent instruction file used by that IDE.
The prompt must tell the agent to read `spawn/navigation.yaml` first and explain
how to use it: read all `read-required` entries before work, inspect
`read-contextual` entries by description, and read contextual files only when
they are relevant to the current task.

`detect(targetRoot)` returns `DetectResult`: `used-in-repo` (whether this repo
already looks like it uses that IDE) plus `capabilities` (see `spec/design/ide-adapters.md`).
There is no separate warning list on the result.

A coordination layer calls `ide.Get(name).add_skills`,
`ide.Get(name).remove_skills`, and equivalent operations.

Spawn ships **concrete** adapters for Cursor, Codex, Claude Code, Windsurf,
GitHub Copilot, and Gemini CLI. Additional IDE targets may be documented in
`spec/design/ide-adapters.md` before an adapter is added to the canonical key list.

The IDE adapter contract should be captured in a table during implementation:

```text
IDE | skill destination | MCP config path | agent ignore file | entry point
```

Every adapter must implement the same logical operations even when the concrete
IDE supports only a subset. Unsupported operations produce warnings and leave
metadata unchanged for that operation.

## Extension Setup Modules

Extension-specific script runners:

- `run-before-install-scripts(extension)`
- `run-after-install-scripts(extension)`
- `run-before-uninstall-scripts(extension)`
- `run-after-uninstall-scripts(extension)`
- `run-healthcheck-scripts(extension)`

If no script is configured for a phase, the runner does not run anything for
that phase. If a script **is** configured in `config.yaml` for a phase, that
script **must** be executed when that phase runs; a failed run uses the blocking
vs warning rules below.

Install and update treat `before-install` failures as **blocking** (`SpawnError`)
because they run before repository mutations. `after-install` failures are
**warnings** after rendered state has been refreshed.

Uninstall: if `before-uninstall` is **omitted** from config, skip that phase. If
it **is** set, the script **must** run and its failure is **blocking**
(`SpawnError`) before further uninstall steps. `after-uninstall` failures are
**warnings**. Healthcheck failure returns a non-zero health result but does not
mutate repository state.

Setup scripts run with the target repository root as the working directory.
Spawn passes the installed extension path, extension name, current version, and
target version through arguments or environment variables defined by the script
runner contract. Immediately before each hook or healthcheck subprocess, Spawn
prints to **stderr** `spawn: running {phase} script: {filename}` (see
`utility-method-flows.md` setup scripts section).

## High-Level Modules

`refresh-gitignore()` rebuilds Spawn-managed `.gitignore` entries from all
installed extensions.

```text
new = all get-ext-git-ignore(extension)
existing = get-git-ignore-list()
save-git-ignore-list(new)
push-to-global-gitignore(new - existing)
remove-from-global-gitignore(existing - new)
```

`refresh-rules-navigation()` calls `save-rules-navigation()` only (see Low-Level
Modules). Used when only local `spawn/rules/` changed relative to navigation.

`refresh-agent-ignore(ide)` calls **`refresh-core-agent-ignore(ide)`** then
**`refresh-extension-agent-ignore(ide)`**. Native ignore adapters rewrite the
core and extension regions independently (full replace per region); extension
metadata stores the extension merge only. Project-style adapters re-diff the
full merged list into IDE config. Legacy `# spawn:start` … `# spawn:end` blocks
in ignore files are dropped when refreshing.

`refresh-skills(ide, extension)` removes old rendered skills for the extension,
generates fresh skill metadata, renders through the IDE adapter, and saves the
new rendered paths.

`refresh-mcp(ide, extension)` removes old rendered MCP entries for the
extension, normalizes `mcp.json`, renders through the IDE adapter, and saves the
new rendered MCP names.

`refresh-entry-point(ide)` builds the standard Spawn entry point prompt and
calls `ide.Get(ide).rewrite-entry-point(prompt)`. The prompt points the IDE
agent at `spawn/navigation.yaml` and explains required and contextual reads.

`remove-skills(ide, extension)` removes paths recorded in
`rendered-skills.yaml`.

`remove-mcp(ide, extension)` removes names recorded in `rendered-mcp.yaml`.

`refresh-extension(ide, extension)` merges MCP for the named extension on that
IDE, re-renders **skills for every installed extension** on that IDE (skill
metadata merges global reads across all extensions), then refreshes agent
ignore for that IDE.

`remove-extension(ide, extension)` removes MCP, skills, agent-ignore entries,
and rendered metadata for one IDE.

`refresh-extension(extension)` runs before-install scripts, refreshes MCP for
the named extension on each initialized IDE, re-renders **all extensions'
skills** on each IDE, refreshes global agent/git ignore and navigation, updates
entry points, then runs after-install scripts.

`remove-extension(extension)` runs before-uninstall scripts, removes rendered
outputs for every initialized IDE, runs after-uninstall scripts, removes the
installed extension folder, then refreshes ignores and navigation so rebuilt
global state no longer includes the removed extension, updates agent ignore and
entry points, and **re-renders skills for each remaining extension** on every
IDE so peer mandatory reads drop removed globals.

`update-extension(extension)` reads **`spawn/.extend/{extension}/source.yaml` only**:
the CLI does **not** take a new source path argument. It re-resolves the stored
source (git / zip / local), validates the candidate **version** string from the
new source against the version recorded for install (see Download And Install),
preserves artifact paths, replaces static extension source, runs setup scripts,
and refreshes navigation, skills, MCP, ignores, and entry points. Downgrades /
same-version no-ops follow the version rules in Download And Install. Changing to
a **different** source identity than `source.yaml` is **not** allowed through
`update-extension`; the user must **`spawn extension remove`** then
**`spawn extension add`** with the new source.

`extension-healthcheck(extension)` checks required files such as
`config.yaml`, validates referenced skills, MCP config, setup scripts, and
declared files/folders.

`extension_init(path, name)` creates a development extension skeleton at
`{path}/extsrc/`. It creates `config.yaml`, `skills/`, `files/`, and `setup/`
when missing. The generated config includes `name`, `schema`, `version`, and
empty sections for files, folders, ignores, skills, and setup. The command must
not overwrite existing author files; if `extsrc/config.yaml` already exists it
emits a warning and leaves it unchanged.

`extension_check(path)` validates an extension source without installing it. It
checks that `extsrc/config.yaml` exists, that referenced skills exist under
`extsrc/skills/`, referenced setup scripts exist under `extsrc/setup/`, declared
files either exist under `extsrc/files/` or are clearly script-created, folder
and file modes use valid enum values, read flags use valid enum values,
required/auto reads have descriptions, `mcp.json` is parseable when present,
and no copied files are left undeclared except as warnings in non-strict mode.

`extension_from_rules(source, outputPath, name, branch)` creates extension
source from an existing target repository. `source` may be a local path, git
URL, or zip URL. Git sources may use `branch`. The command resolves the source
into `spawn/.metadata/temp/{operation_id}/` when staging is needed (see Temporary download
staging), reads `spawn/rules/` and
`spawn/navigation.yaml` from that target repository, then writes a new
`{outputPath}/extsrc/` tree for extension authoring.

`add-ide(ide)` adds the IDE to `spawn/.metadata/ide.yaml`, initializes IDE
metadata, calls `detect(targetRoot)` for that adapter, prints **warnings** if
`capabilities.skills` or `capabilities.mcp` are insufficient for Spawn's
repository-scoped rendering (see `ide-adapters.md`), then refreshes the IDE entry
point, refreshes skills for every installed extension, refreshes MCP for every
installed extension, and refreshes agent-ignore for that IDE.

`remove-ide(ide)` removes Spawn-rendered MCP and skills for every installed
extension, removes Spawn-managed agent-ignore entries, then removes the IDE from
`spawn/.metadata/ide.yaml`.

## Download And Install

### Temporary download staging

Commands that materialize a remote or archive source (git clone, zip extract, or
similar) **must** stage files under:

```text
spawn/.metadata/temp/{operation_id}/
```

relative to the target repository root. `operation_id` is a freshly generated UUID (or equivalent uniqueness) **per
staging operation** (for example one id per `download-extension` invocation
that needs a staging directory). Local path sources do not need this directory
unless an implementation chooses to copy via staging for consistency.

**Zip extraction** must refuse path traversal (reject entries whose resolved path
escapes the staging directory). Tests must cover a malicious archive.

The CLI **must** remove `spawn/.metadata/temp/{operation_id}/` after the operation
finishes, whether it succeeds or fails (for example `try` / `finally`), so
aborted runs do not rely on manual cleanup. Stale directories from crashes may
remain; they are safe to delete by the user. `spawn init` **must** ensure
`spawn/.metadata/temp/` is covered by Spawn-managed root `.gitignore` patterns so staged
content is not committed.

### Install and build

`download-extension(path, branch)` resolves a git or zip source into
`spawn/.metadata/temp/{operation_id}/` as above. It validates `extsrc/config.yaml`, checks for file conflicts with
other installed extensions, checks version/source rules, then copies `extsrc/`
to `spawn/.extend/{extension}`.

**Source identity:** when an extension is **already** installed, `source.yaml`
records the authoritative source. `extension add` with a candidate source that
**does not match** that record must **`SpawnError` before any mutation** — the
only way to switch sources is **`spawn extension remove`** followed by
**`spawn extension add`** with the new source.

**Version strings:** `config.yaml` carries a plain `version` string. Spawn
compares versions **in-process** without adding a third-party dependency (for
example split on `.`, compare numeric segments left to right, trailing non-numeric
suffix compared lexicographically, or another deterministic rule documented next
to the helper). No external **packaging** / dependency solver is required.

If the candidate version is **not newer** than the installed version per that
rule, `SpawnError`. If an older installed tree is being replaced by a strictly
newer candidate and source identity matches, proceed after checks.

After a successful copy, Spawn writes `source.yaml` with the source path,
branch, and resolved revision or artifact identity.

`install-extension(path, branch)` downloads an extension and then refreshes it.

`list-extensions(buildPath, branch)` resolves a build source, reads
`extensions.yaml`, and returns extension path/branch entries.

`install-build(path, branch)` downloads all extensions listed in the build
manifest and refreshes each installed extension.

## Lifecycle Semantics

Extension install follows this order:

1. Resolve source into `spawn/.metadata/temp/{operation_id}/` when staging is required.
2. Validate `extsrc/config.yaml`, skills, files, folders, setup scripts, and
   MCP definitions.
3. Check version, source identity, cross-extension path collisions, and
   **cross-extension rendered identity** (normalized skill names and MCP server
   names from the candidate must not duplicate names from any **other** already
   installed extension).
4. Run blocking `before-install` scripts from the candidate source when
   configured.
5. Copy extension source into `spawn/.extend/{ext}` and write `source.yaml`.
6. Materialize declared static and artifact files into the target repository.
7. Refresh navigation, gitignore, agent ignores, skills, MCP, and entry points.
8. Run `after-install` scripts and report warnings.

Extension uninstall follows this order:

1. Run `before-uninstall` scripts **when configured** — if the key is absent,
   skip this step; if present, failure **`SpawnError`** **aborts** the command
   before further steps.
2. Remove Spawn-rendered MCP and skills for every initialized IDE.
3. Remove static files and folders returned by `get-removable(extension)`.
4. Preserve artifact files and folders.
5. Remove the installed extension source folder.
6. Refresh navigation, gitignore, agent ignores, and entry points.
7. Run `after-uninstall` scripts and report warnings.

Commands should avoid partial ownership updates. When a failure happens after a
mutation, the command reports the completed phase and the next recommended
repair command, usually `spawn extension update {extension}` or **`spawn refresh`**.
Future implementations may add transactional rollback, but the baseline design
relies on **metadata-driven refresh** to converge after recoverable failures
(Core Rules: **Refresh ordering and recovery**).

## Public Commands

The CLI uses Python `argparse`-style subcommands. Command names use words and
nested resources instead of mixing flag-only commands with dash-composed command
names.

`spawn init` creates the core `spawn/` structure and ensures `spawn/.metadata/temp/` is
gitignored (see Temporary download staging).

`spawn ide add {ide1} {ide2} ...` adds IDEs to the target repository and
refreshes rendered state for each one.

`spawn ide remove {ide1} {ide2} ...` removes Spawn-rendered state for IDEs and
then removes them from `spawn/.metadata/ide.yaml`.

`spawn ide list` lists initialized IDEs.

`spawn ide list-supported-ides` requires **`spawn init`** like every other
command. It uses the current working directory as `targetRoot`, invokes
`detect_supported_ides`, and prints YAML to stdout. For each canonical IDE key in
`supported_ide_keys()` order, one nested mapping containing `used-in-repo` and
`capabilities`. Example shape:

```yaml
cursor:
  used-in-repo: true
  capabilities:
    skills: native
    mcp: project
    agentIgnore: native
    entryPoint: agents-md
codex:
  used-in-repo: false
  capabilities:
    skills: native
    mcp: project
    agentIgnore: unsupported
    entryPoint: agents-md
```

It uses the same **non-blocking Spawn lock** as all other commands (Core Rules).

`spawn refresh` replaces `spawn/.core/config.yaml` with the bundled default core
config (`version` and `agent-ignore` exactly match the packaged resource;
repository-local edits to core config are not preserved), after validating that
the existing file parses as `CoreConfig`, then rebuilds MCP,
skills, agent-ignore, extension navigation and rules navigation, gitignore
metadata, and IDE entry points for every IDE registered in `spawn/.metadata/ide.yaml`.
It does **not** run extension install/uninstall setup scripts. Requires
**`spawn init`**. Mutating; acquires the Spawn lock. If any MCP merge produces
rendered servers, **stdout** may print **`MCP_MERGED_NOTICE`** at most once for
the command.

`spawn rules refresh` rescans `spawn/rules/` and updates rule entries in
`spawn/navigation.yaml` via `save-rules-navigation()`. Requires an initialized
target (`spawn init`). Mutating; acquires the Spawn lock. Does not reinstall
extensions, refresh IDE skills, or rewrite entry points — only the **rules**
section of navigation.

`spawn extension add "path" [--branch "branch"]` installs an extension from a
local path, git URL, or zip URL.

`spawn extension update "extensionName"` updates an installed extension from
its existing `source.yaml`.

`spawn extension remove "extensionName"` uninstalls an extension and removes
only Spawn-owned rendered state and static files.

`spawn extension list` lists installed extensions.

`spawn extension init [path] --name "extension-name"` creates a new `extsrc/`
skeleton for extension development. `path` defaults to the current directory.

`spawn extension check [path]` validates an extension source structure without
installing it. `path` defaults to the current directory. It is intended for
local authoring and CI checks.

`spawn extension from-rules "source" --name "extension-name" [--branch "branch"] [--output "path"]`
creates extension source from an existing target repository. `source` may be a
local path, git URL, or zip URL. The output path defaults to the current
directory.

`spawn extension healthcheck "extensionName"` runs extension health validation
and the optional healthcheck setup script.

`spawn build install "path" [--branch "branch"]` installs or refreshes
extensions from a build manifest source.

`spawn build list "path" [--branch "branch"]` resolves a build manifest and
prints the extension sources it contains.

Compound workflows are expressed by running commands sequentially. For example,
initializing a repository and installing a build is `spawn init` followed by
`spawn build install "path"`. Initializing and adding IDEs is `spawn init`
followed by `spawn ide add {ide}`.

## Rebuild Semantics

Rebuilds follow the phase order in **Refresh ordering and recovery** under Core
Rules: validate the candidate, remove using prior metadata, add, then persist
metadata after a successful add.

Skill rebuild always removes previous Spawn-rendered skills first, using
`rendered-skills.yaml`, then renders new skills from current extension config.

MCP rebuild always removes previous Spawn-rendered MCP entries first, using
`rendered-mcp.yaml`, then renders current normalized MCP definitions.

Ignore rebuilds compare previous metadata lists with newly computed lists and
apply only additions/removals owned by Spawn.

Navigation rebuilds replace extension sections from current extension config
and synchronize local rules from `spawn/rules/`.

Entrypoint rebuilds rewrite only the Spawn-managed block inside an IDE
entrypoint when the adapter supports block-level ownership. If an IDE requires
a whole-file entrypoint, Spawn warns before overwriting and records that
behavior in adapter-specific implementation docs.
