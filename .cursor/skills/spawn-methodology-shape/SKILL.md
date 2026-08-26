---
name: spawn-methodology-shape
description: Design methodology namespaces, static vs artifact layout, and read surfaces before packing.
---


Goal: before editing YAML heavily, decide what the methodology teaches and where files live under `extsrc/files/`.

1. Define audiences (human vs agent) and primary workflows; map each to concrete paths under a single namespace prefix.
2. Classify each deliverable as `static` (canonical methodology the pack maintains) vs `artifact` (per-repo living documents).
3. Choose what belongs in global navigation (`globalRead`) vs only when using this pack’s skills (`localRead`).
4. Split long specs into `extsrc/files/` and keep `extsrc/skills/*.md` as thin procedures that point to those reads.
5. Align names with uniqueness rules (prefixed skill ids, MCP server ids, path prefixes) if this pack coexists with others.
6. Implement the tree under `extsrc/files/`, then run `spawn-ext-config` and `spawn-ext-verify` workflows.
7. **Version:** If namespaces, static vs artifact split, or read surfaces change shipped methodology, **prompt** the author to bump **`version`** via **`spawn-ext-increment-version`** before consumers upgrade.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spawn-ext-guide/ai/core.md` - Machine baseline — terms, extsrc tree rules, static vs artifact, name and uniqueness, install outputs.
- `spawn-ext-guide/ai/config-yaml.md` - Machine schema for config.yaml — keys, files/folders/skills modes, reads, ignores, setup, annotated example.
- `spawn-ext-guide/user-guide.md` - Human-readable standalone guide — narrative for all authoring topics.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spawn-ext-guide/ai/skill-sources.md` - Machine rules for extsrc/skills/*.md — frontmatter, name/description resolution, rendered skill shape, example.
- `spawn-ext-guide/ai/mcp-json.md` - Machine schema for extsrc/mcp/windows.json, linux.json, macos.json — servers, OS selection, aligned name sets, transport, spawn_stdio_proxy (stdio IDE proxy), env, capabilities, validation against check, JSON examples.
- `spawn-ext-guide/ai/cli.md` - Machine CLI reference — spawn init/extension/build commands, extensions.yaml bundle shape, authoring checklist.
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
