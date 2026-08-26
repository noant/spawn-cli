---
document: spawn-extension-author-core
audience: machine
encoding: utf-8
---

# Spawn extension — core model

## authoring_context

- **Extension source tree** (what you edit while authoring): `<extension-repo>/extsrc/` — `config.yaml`, mirror templates under `extsrc/files/`, skill sources under `extsrc/skills/`, optional **`extsrc/mcp/*.json`** (per-platform MCP), `setup/*.py`.
- **Target repo** (consumer): paths under `files:` / `folders:` are relative to the **target root** after install (e.g. `spec/guide.md`), not `extsrc/files/spec/guide.md`. Templates live only under `extsrc/files/` in the **source** pack.

## vocabulary

- `extension`: installable pack (templates, optional skills, MCP, Python setup hooks, ignore rules).
- `extension_repository`: git repo, folder, or zip containing directory `extsrc/`.
- `target_repository`: repo where `spawn init` and `spawn extension add` run; outputs include `spawn/.extend/<name>/`.

## content_classes

- `static`: safe for tool to overwrite on extension update.
- `artifact`: project-owned; MUST NOT be overwritten on update after first materialization.
- `rendered_outputs`: navigation index, IDE skills, IDE MCP fragments; produced by Spawn from declarations.

## directory_layout

```
<extension-repo>/
  extsrc/
    config.yaml    # REQUIRED
    mcp/           # OPTIONAL — windows.json, linux.json, macos.json (cross-platform MCP)
    skills/*.md    # OPTIONAL; filename = key under config.skills when declared
    files/...      # mirrors paths under config.files
    setup/*.py     # OPTIONAL lifecycle scripts
```

constraints:

- ONLY `extsrc/` is copied into target as installed extension.
- `extsrc/config.yaml`: REQUIRED.
- Every path under `extsrc/files/` MUST appear as key under `config.files`.
- `spawn extension check . --strict`: undeclared files under `extsrc/files/` → ERROR.

## extension_identity

- config field `name`: stable id; convention kebab-case lowercase.
- install path: `<target-root>/spawn/.extend/<name>/`.
- If `name` omitted: install MAY use fallback `extension`; authoring MUST set `name` explicitly and keep stable.
- manifest format: top-level `schema` integer MUST be `1` for the current `config.yaml` format.

## uniqueness_constraints.target_wide

- normalized skill `name`: UNIQUE across all extensions in one target.
- MCP `servers[].name` (in **`extsrc/mcp/*.json`**, unified name set across platforms): UNIQUE across all extensions in one target.
- naming convention: prefix ids (`acme-run-task`, `acme-docs-mcp`) to reduce collisions.
- `files` / `folders` paths SHOULD use namespaces so multiple extensions do not clash.

## target_materialization.after_spawn_extension_add

execution_context: target repo root after `spawn init`.

outputs_sequence:

1. full copy `extsrc/` → `<target>/spawn/.extend/<name>/`
2. materialize `extsrc/files/` templates per `files` entries and static/artifact rules
3. Spawn metadata and IDE outputs (adapter-specific paths): `spawn/navigation.yaml`, rendered skills, merged MCP, agent-ignore fragments as per adapters.

exact IDE paths/formats: adapter-dependent; derived only from `config.yaml`, skill sources, and **`extsrc/mcp/*.json`** for the host OS.

## sibling_machine_docs

- `spawn-ext-guide/ai/config-yaml.md` — full `config.yaml` schema, annotated example.
- `spawn-ext-guide/ai/skill-sources.md` — `extsrc/skills/*.md` format, frontmatter, rendering.
- `spawn-ext-guide/ai/mcp-json.md` — `extsrc/mcp/*.json` schema and examples.
- `spawn-ext-guide/ai/cli.md` — Spawn CLI, `extensions.yaml`, authoring checklist.
- `spawn-ext-guide/user-guide.md` — human-readable narrative (same topics).
