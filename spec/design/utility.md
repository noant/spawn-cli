# Utility

This document describes how the Spawn CLI transforms a target repository. It is
about command semantics and directory mutations, not parser implementation.

## Core Rules

All paths handled by modules are relative to the target repository root.

If a file or directory under `spawn/.metadata/` is missing, Spawn creates it on
demand.

Spawn removes only entries it owns. Ownership is recorded in:

- `spawn/.metadata/git-ignore.txt`;
- `spawn/.metadata/{ide}/agent-ignore.txt`;
- `spawn/.metadata/{ide}/rendered-skills.yaml`;
- `spawn/.metadata/{ide}/rendered-mcp.yaml`.

Commands should be idempotent whenever they describe a desired repository
state. Re-running `spawn init`, adding an already listed IDE, refreshing an
installed extension, or rebuilding skills should converge to the same rendered
state without duplicating metadata or ignore entries.

Mutating commands should acquire a repository-local Spawn lock before changing
files. The lock prevents concurrent installs, updates, rebuilds, and IDE
refreshes from interleaving metadata writes. Read-only commands do not require
the lock.

Warnings report recoverable inconsistencies such as an already existing
rendered skill that Spawn will overwrite, an IDE without MCP support, or a
missing optional setup script. Errors stop the command before the next mutation
when continuing could corrupt ownership state, overwrite another extension's
files, or install an unsupported config schema.

## Supported IDE keys

The Spawn CLI keeps a **static ordered list** of canonical IDE keys (one frozen
constant in code). It must stay aligned with the Adapter Registry in
`spec/design/ide-adapters.md`: each key must have a registered adapter at
`ide.Get(key)`. User-facing aliases (`claude` → `claude-code`, etc.) apply only
when parsing commands; this list contains canonical identifiers only.

```yaml
# Canonical keys — illustrative order matches Adapter Registry
- cursor
- codex
- qoder
- claude-code
- qwen-code
- windsurf
- github-copilot
- aider
- zed
- gemini-cli
- devin
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
comes from CLI resources.

`add-ide-to-list(ide)` adds an IDE to `spawn/.metadata/ide.yaml`.

`remove-ide-from-list(ide)` removes an IDE from `spawn/.metadata/ide.yaml`.

`list-extensions()` returns folder names under `spawn/.extend/`.

`list-ides()` returns IDE names from `spawn/.metadata/ide.yaml`.

`get-required-read-global(extension)` reads
`spawn/.extend/{extension}/config.yaml` and returns files with
`globalRead: required`.

`get-required-read-global()` calls the extension-specific function for every
installed extension and returns a list grouped by extension.

`get-required-read-ext-local(extension)` returns files with
`localRead: required`.

`get-auto-read-global(extension)` returns files with `globalRead: auto`.

`get-auto-read-global()` calls the extension-specific function for every
installed extension and returns a list grouped by extension.

`get-auto-read-local(extension)` returns files with `localRead: auto`.

Each read function returns file path and description.

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

`get-agent-ignore-list(ide)` and `save-agent-ignore-list(ide, items)` read and
replace `spawn/.metadata/{ide}/agent-ignore.txt`.

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

## Normalized MCP Shape

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

`add-skills` receives `skill-metadata[]` and writes IDE-specific skills. If the
destination skill already exists, Spawn warns and overwrites it.

`remove-skills` receives rendered skill paths and deletes only those paths.

`add-mcp` and `remove-mcp` add or remove MCP entries. If an IDE does not support
MCP, the adapter emits a warning.

`add-agent-ignore` and `remove-agent-ignore` mutate the IDE-specific ignore file
with the given globs.

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

Supported IDE adapter targets are Cursor, Codex, Qoder, Claude Code, Qwen Code,
Windsurf, GitHub Copilot, Aider, Zed, Gemini CLI, and Devin. Their exact skill
folders, MCP formats, and shared agent files such as `AGENTS.md` should be
specified in IDE-specific design or implementation tasks.

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

If no script is configured, the runner returns. If a script fails, Spawn emits
a warning unless the command defines that phase as blocking.

Install and update treat `before-install` failures as blocking because they run
before repository mutations and usually validate prerequisites. `after-install`
failures are warnings after rendered state has been refreshed. Uninstall treats
`before-uninstall` failures as blocking only when the script explicitly marks
itself as required; otherwise uninstall continues with a warning. Healthcheck
failure returns a non-zero health result but does not mutate repository state.

Setup scripts run with the target repository root as the working directory.
Spawn passes the installed extension path, extension name, current version, and
target version through arguments or environment variables defined by the script
runner contract.

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

`refresh-agent-ignore(ide)` rebuilds IDE agent ignore entries from core ignore
globs and all extension agent-ignore globs.

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

`refresh-extension(ide, extension)` refreshes MCP, skills, and agent ignore for
one IDE.

`remove-extension(ide, extension)` removes MCP, skills, agent-ignore entries,
and rendered metadata for one IDE.

`refresh-extension(extension)` runs before-install scripts, refreshes the
extension for every initialized IDE, refreshes global agent/git ignore and
navigation, then runs after-install scripts.

`remove-extension(extension)` runs before-uninstall scripts, removes rendered
outputs for every initialized IDE, runs after-uninstall scripts, removes the
installed extension folder, then refreshes ignores and navigation so rebuilt
global state no longer includes the removed extension.

`update-extension(extension)` reads `spawn/.extend/{extension}/source.yaml`,
downloads the same source, validates the candidate version, preserves artifact
paths, replaces static extension source, runs migration-capable setup scripts,
and refreshes navigation, skills, MCP, ignores, and entry points. Updating to
the same or an older version is an error unless the command explicitly supports
force reinstall in a future extension.

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
into a temporary folder when needed, reads `spawn/rules/` and
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

`download-extension(path, branch)` resolves a git or zip source into a temporary
local folder. It validates `extsrc/config.yaml`, checks for file conflicts with
other installed extensions, checks version/source rules, then copies `extsrc/`
to `spawn/.extend/{extension}`.

If the same version or a newer version already exists, Spawn errors. If an older
version exists, Spawn replaces the installed extension source after source
identity checks. If existing `source.yaml` points to a different source, Spawn
errors before replacing files.

After a successful copy, Spawn writes `source.yaml` with the source path,
branch, and resolved revision or artifact identity.

`install-extension(path, branch)` downloads an extension and then refreshes it.

`list-extensions(buildPath, branch)` resolves a build source, reads
`extensions.yaml`, and returns extension path/branch entries.

`install-build(path, branch)` downloads all extensions listed in the build
manifest and refreshes each installed extension.

## Lifecycle Semantics

Extension install follows this order:

1. Resolve source into a temporary folder.
2. Validate `extsrc/config.yaml`, skills, files, folders, setup scripts, and
   MCP definitions.
3. Check version, source identity, and cross-extension path collisions.
4. Run blocking `before-install` scripts from the candidate source when
   configured.
5. Copy extension source into `spawn/.extend/{ext}` and write `source.yaml`.
6. Materialize declared static and artifact files into the target repository.
7. Refresh navigation, gitignore, agent ignores, skills, MCP, and entry points.
8. Run `after-install` scripts and report warnings.

Extension uninstall follows this order:

1. Run `before-uninstall` scripts.
2. Remove Spawn-rendered MCP and skills for every initialized IDE.
3. Remove static files and folders returned by `get-removable(extension)`.
4. Preserve artifact files and folders.
5. Remove the installed extension source folder.
6. Refresh navigation, gitignore, agent ignores, and entry points.
7. Run `after-uninstall` scripts and report warnings.

Commands should avoid partial ownership updates. When a failure happens after a
mutation, the command reports the completed phase and the next recommended
repair command, usually `spawn extension update {extension}` or a full refresh command.
Future implementations may add transactional rollback, but the baseline design
relies on metadata-driven refresh to converge after recoverable failures.

## Public Commands

The CLI uses Python `argparse`-style subcommands. Command names use words and
nested resources instead of mixing flag-only commands with dash-composed command
names.

`spawn init` creates the core `spawn/` structure.

`spawn ide add {ide1} {ide2} ...` adds IDEs to the target repository and
refreshes rendered state for each one.

`spawn ide remove {ide1} {ide2} ...` removes Spawn-rendered state for IDEs and
then removes them from `spawn/.metadata/ide.yaml`.

`spawn ide list` lists initialized IDEs.

`spawn ide list-supported-ides` does **not** require `spawn init`. It uses the
current working directory as `targetRoot`, invokes `detect_supported_ides`,
and prints YAML to stdout. For each canonical IDE key from `supported_ide_keys`,
one nested mapping containing `used-in-repo` and `capabilities`. Example shape:

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

Read-only; does not acquire the Spawn lock.

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
