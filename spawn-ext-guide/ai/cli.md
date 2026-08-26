---
document: spawn-extension-cli
audience: machine
encoding: utf-8
prerequisite: spawn-ext-guide/ai/core.md for install outputs and layout
---

# Spawn CLI and distribution

## cli.reference

cwd: target repo root for most commands (no typical `--target` flag).

prerequisite: target MUST be `spawn init` before extension install commands (except commands only touching extension source tree).

extension_authoring:

- `spawn extension init . --name <id>`: skeleton `extsrc/`, empty `config.yaml`, empty **`extsrc/mcp/*.json`** (`windows`, `linux`, `macos`)
- `spawn extension check .`: validate; `--strict` elevates to errors (missing listed skills, undeclared files under `extsrc/files/`, missing descriptions when read flags set, invalid or mismatched **`extsrc/mcp/*.json`** including **`spawn_stdio_proxy`** without **`stdio`** transport, stray obsolete **`extsrc/mcp.json`**, missing setup scripts when referenced)
- `spawn extension from-rules <source> --name <id> --output <dir>`: bootstrap from repo `spawn/rules/`

target_install:

- `spawn extension add <path-or-url> [--branch BR]`
- `spawn extension list`
- `spawn extension update <name>`
- `spawn extension remove <name>`
- `spawn extension healthcheck <name>` when `setup.healthcheck` is set

bundled_install:

- `spawn build install <path-or-url> [--branch BR]`: install every extension from `extensions.yaml` at that source root.

initializer:

- `spawn init`: create `spawn/` in current repo.

## extensions_yaml.bundle_manifest

purpose: list multiple extension sources for single build command.

shape:

```yaml
extensions:
  - path: https://example.com/org/ext-a.git
    branch: main
  - path: https://example.com/org/ext-b.git
  - path: /absolute/or/relative/path/to/ext-src-or-repo
```

constraint: each entry resolves to tree containing `extsrc/` with `config.yaml`; resolution same family as `spawn extension add`.

## authoring_procedure.checklist

1. `spawn extension init . --name <pack-id>`
2. add templates under `extsrc/files/`; declare every path in `files` with correct `mode`, `globalRead`, `localRead`
3. add `extsrc/skills/*.md`; register each filename under `skills` when overrides or `required-read` needed
4. optional **`extsrc/mcp/windows.json`**, **`linux.json`**, **`macos.json`** — each top-level **`servers`**; identical server **`name`** sets across platforms
5. optional `extsrc/setup/*.py` referenced from `setup`
6. `spawn extension check . --strict`
7. disposable target: `spawn init`; `spawn extension add <source>`; configure IDE if needed; verify navigation/skills
8. distribute repo or zip for consumers (`spawn extension add` or `extensions.yaml` entry)
9. after substantive packaging changes (templates under `extsrc/files/`, `skills`, **`extsrc/mcp/*.json`**, `files:`/`folders:`/`setup`/ignores): **prompt** author to bump **`version`** in **`extsrc/config.yaml`** using **`spawn-ext-increment-version`** before tagging or publishing (skip only for trivial typo-only edits with no consumer-visible behavior change)
