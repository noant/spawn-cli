# Data Structure

This document defines the Spawn data layout for target repositories and
extension authoring repositories. All stored paths are relative to the target
repository root that contains `spawn/`.

## Target Repository Layout

Spawn creates this structure inside the repository where AIDD will be used:

```text
target-repo/
  spawn/
    navigation.yaml
    rules/
      {file}.yaml
    .core/
      config.yaml
    .metadata/
      ide.yaml
      git-ignore.txt
      temp/
        {operation_id}/
          …
      {ide}/
        rendered-mcp.yaml
        rendered-skills.yaml
        agent-ignore.txt
    .extend/
      {ext}/
        config.yaml
        source.yaml
        mcp.json
        skills/
          {skill}.md
        files/
          {any-path}
        setup/
          {script}.py
```

The local `spawn-cli` repository does not reproduce this runtime tree as active
state. The CLI creates it inside a target repository.

**Operational alignment:** the CLI uses the **current working directory** as the
target repository root (no `--target`). File `spawn/.metadata/.spawn.lock`
serializes **all** commands with **non-blocking** acquisition; missing `spawn/`
before any command except `spawn init` is an error (**`need init before`**). See
`spec/design/utility.md` (Core Rules).

`spawn/.metadata/temp/{operation_id}/` is ephemeral staging for git clones, zip
extracts, and similar download steps inside an initialized target repository.
Each `operation_id` is unique per staging operation; the CLI removes that
directory when the operation ends. See `spec/design/utility.md` (Temporary
download staging). `spawn/.metadata/temp/` **must** be gitignored; it is not
agent-facing context (and stays under `spawn/**` for core `agent-ignore`).

`spawn/navigation.yaml` is the main agent-facing navigation file. It is rebuilt
from installed extension configs and local `spawn/rules/` entries.

`spawn/.core/config.yaml` is the core Spawn config. It contains the core version
and core `agent-ignore` globs. The default core ignore list must hide all of
`spawn/` from IDE agents except `spawn/rules/` and the agent-facing navigation
surface.

`spawn/.metadata/ide.yaml` lists initialized IDEs. IDE-specific rendered state
is stored under `spawn/.metadata/{ide}/`.

`spawn/.metadata/{ide}/rendered-mcp.yaml` records MCP entries rendered by Spawn
for one IDE. It exists so refresh and uninstall can remove only Spawn-managed
MCP entries and leave user-managed MCP configuration untouched.

`spawn/.metadata/{ide}/rendered-skills.yaml` records skill files rendered by
Spawn for one IDE. It exists so refresh and uninstall can remove stale
Spawn-managed skill files without deleting user skills.

`spawn/.metadata/{ide}/agent-ignore.txt` stores the merged Spawn-managed ignore
patterns rendered into the IDE-specific agent ignore file.

`spawn/.metadata/git-ignore.txt` stores the merged Spawn-managed `.gitignore`
patterns. It is the ownership record for gitignore refresh and uninstall.

`spawn/.extend/{ext}` is the installed copy of an extension. It must be ignored
by IDE agents because it is source/cache for the utility, not the active
agent-facing instruction surface.

`spawn/rules/{file}.yaml` stores local target-repository rules. Users own these
files. `save-rules-navigation()` adds missing rule files to
`navigation.yaml` and removes navigation entries whose files no longer exist.

## Core Config Shape

`spawn/.core/config.yaml`:

```yaml
version: "0.1.0"
agent-ignore:
  - spawn/**
  - "!spawn/navigation.yaml"
  - "!spawn/rules/**"
```

The exact core version follows the installed CLI/core package. Ignore globs use
the same practical ignore syntax described below.

## Metadata Shapes

`spawn/.metadata/ide.yaml` is the canonical list of initialized IDE adapters:

```yaml
ides:
  - codex
  - cursor
```

The list is unique and ordered by first addition. Removing an IDE removes only
the IDE name from this file after Spawn-managed rendered outputs for that IDE
have been removed.

`spawn/.extend/{ext}/source.yaml` records where the installed extension came
from:

```yaml
extension: spectask
source:
  type: git
  path: https://example.com/org/spectask.git
  branch: main
  resolved: 7f3a1c2
installed:
  version: "1.0.0"
  installedAt: "2026-04-29T00:00:00Z"
```

`source.type` may be `git`, `zip`, or `local`. `resolved` is a commit, archive
digest, or local copy identity when available. Update commands use this file to
resolve the next extension source and to reject replacement from an unrelated
source unless the user explicitly reinstalls.

## Extension Repository Layout

An extension development repository stores the extension source under
`extsrc/`:

```text
extend-repo/
  extsrc/
    config.yaml
    mcp.json
    skills/
      {skill}.md
    files/
      {any-path}
    setup/
      {script}.py
```

Installing an extension copies the full `extend-repo/extsrc/` tree into
`target-repo/spawn/.extend/{ext}/`. After the copy, Spawn writes
`spawn/.extend/{ext}/source.yaml` with the source path, branch, or downloaded
artifact reference used for the install.

## Extension Config Shape

`extsrc/config.yaml` and the installed
`spawn/.extend/{ext}/config.yaml` use the same shape:

```yaml
name: spectask
version: "1.0.0"
schema: 1
files:
  spec/main.md:
    description: Spec task process.
    mode: static
    globalRead: required
    localRead: required
  spec/design/hla.md:
    description: High-level architecture.
    mode: artifact
    globalRead: auto
    localRead: auto
folders:
  spec/tasks:
    mode: artifact
agent-ignore:
  - spawn/.extend/**
git-ignore:
  - .spawn-cache/**
skills:
  spectask-execute.md:
    name: spectask-execute
    description: Execute approved spectasks.
    required-read:
      - spec/tasks/current/overview.md
setup:
  before-install: bootstrap.py
  after-install: after_install.py
  before-uninstall: before_uninstall.py
  after-uninstall: after_uninstall.py
  healthcheck: healthcheck.py
```

`name` is the stable extension identifier. It should match the installed folder
name under `spawn/.extend/{ext}`. If omitted for legacy extension sources,
Spawn may derive the name from the source folder, but validated extensions
should declare it explicitly.

`schema` is the extension config schema version. Unknown future schema versions
are errors. Unknown fields in the current schema should produce warnings unless
the command runs in strict validation mode.

`files` describes target files created by copying from `extsrc/files/` or by
setup scripts. `mode` defaults to `static`. `globalRead`, `localRead`, and read
flags default to `no`.

`folders` describes target folders created by an extension. Folder `mode`
defaults to `static`.

`skills` references Markdown files under `skills/`. Optional `name` and
`description` override skill frontmatter. Optional `required-read` adds
skill-specific mandatory reads.

`setup` references Python scripts under `setup/`. Every script is optional and
must be idempotent.

Allowed enum values:

- `mode`: `static`, `artifact`
- `globalRead`: `required`, `auto`, `no`
- `localRead`: `required`, `auto`, `no`

Every file that Spawn copies from `extsrc/files/**` should be declared in the
`files` section. During validation, undeclared copied files produce warnings in
normal mode and errors in strict mode. Files declared in config but missing from
`extsrc/files/**` are allowed only when a setup script creates them.

Descriptions are required for files with `globalRead` or `localRead` set to
`required` or `auto`, because rendered navigation and skills need meaningful
context labels.

## Build Manifest Shape

A build repository may contain `extensions.yaml`:

```yaml
extensions:
  - path: https://example.com/org/spectask.git
    branch: main
  - path: https://example.com/org/team-rules.zip
```

Each entry points to an extension source or artifact. `branch` is meaningful
only for git sources. Build manifests do not declare extension content
directly; they only compose installable extension sources.

## Navigation Shape

`spawn/navigation.yaml` is generated from extension configs and local rules:

```yaml
read-required:
  - ext: spectask
    files:
      - path: spec/main.md
        description: Spec task process.
  - rules:
      - path: spawn/rules/team.yaml
        description: Team rules.
read-contextual:
  - ext: spectask
    files:
      - path: spec/design/hla.md
        description: High-level architecture.
  - rules:
      - path: spawn/rules/frontend.yaml
        description: Frontend rules.
```

Extension files with `globalRead: required` go to `read-required`.
Extension files with `globalRead: auto` go to `read-contextual`.
Extension files with `globalRead: no` are not listed globally.

Local rule files from `spawn/rules/` are user-maintained. If a rule file exists
but is absent from navigation, `save-rules-navigation()` adds it to
`read-required -> rules` by default. If navigation references a missing rule
file, Spawn removes the entry and emits a warning.

## Rendered Metadata Shapes

`spawn/.metadata/{ide}/rendered-mcp.yaml`:

```yaml
extensions:
  spectask:
    - name: spectask-db
    - name: spectask-search
```

`spawn/.metadata/{ide}/rendered-skills.yaml`:

```yaml
extensions:
  spectask:
    - skill: spectask-create.md
      path: .agents/skills/spectask-create/SKILL.md
    - skill: spectask-execute.md
      path: .agents/skills/spectask-execute/SKILL.md
```

These files record Spawn ownership only. They are not the source of extension
truth. Rendered skill bodies list mandatory and contextual paths from extension
`localRead` / `globalRead` and from **rules** entries in `spawn/navigation.yaml`
(see `spec/design/agentic-flow.md`).

## Target Files And Extension Files

Files in `extsrc/files/**` are installed into the target repository by
reproducing their path under `files/`, unless the extension config later defines
a more explicit mapping.

Static files and folders are extension-owned. Updates may overwrite them.

Artifact files and folders are target-owned after creation. Updates must not
overwrite them. They may only be changed by explicit migration scripts from the
extension setup folder.

Before installing or updating an extension, Spawn checks for files or folders
claimed by another installed extension. Cross-extension collisions are errors
and must stop the copy before the target repository is mutated.

Path ownership is computed from every installed extension's `files` and
`folders` sections. A file path may have only one extension owner. A folder path
may not overlap another extension's claimed file or folder unless both
extensions explicitly support a future shared-folder contract; the initial
contract treats overlaps as errors.

Existing target files not owned by another extension are handled by mode:

- `static`: Spawn may overwrite on install or update after warning when the
  file already exists and was not previously Spawn-owned.
- `artifact`: Spawn creates the file only when missing. Existing content is
  preserved.

## Local Rules Shape

`spawn/rules/{file}` is target-owned. Rule files may be Markdown, YAML, text, or
any other format meaningful to the team. Spawn does not parse rule file content
and does not require a rule schema.

When `save-rules-navigation()` discovers a rule file that is not yet listed in
navigation, it adds the file to `read-required -> rules` by default with a
generated or placeholder description. Users may then edit `spawn/navigation.yaml`
directly to improve the description or move the rule entry from
`read-required -> rules` to `read-contextual -> rules`.

If a rule file is listed in navigation but no longer exists under
`spawn/rules/`, Spawn removes the navigation entry and emits a warning.

## Core Invariants

- All persisted paths are relative to the target repository root.
- `spawn/.metadata/**` records Spawn ownership and is not methodology source.
- `spawn/.extend/**` is extension source/cache and is not part of the normal
  agent-facing surface.
- `spawn/navigation.yaml`, rendered skills, rendered MCP config, ignore files,
  and IDE entry points are generated outputs.
- Artifact files and folders are target-owned after creation and are not
  overwritten by extension updates.
- Static files and folders are extension-owned and may be rewritten by updates.

## Ignore Glob Contract

Ignore patterns follow practical ignore syntax:

- One line is one rule.
- Empty lines are ignored.
- A leading `#` starts a comment.
- A leading `!` negates a previous ignore rule when the target ignore engine
  supports negation.
- `*` matches any sequence within one path segment.
- `?` matches one character.
- `[...]` matches one character from a set or range.
- `**` matches any number of directories, including zero.
- Directory patterns such as `node_modules/` target directory trees.

Spawn stores config and metadata globs with `/` as the separator. IDE adapters
translate them when an IDE requires another format.
