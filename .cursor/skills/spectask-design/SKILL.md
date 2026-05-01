---
name: spectask-design
description: Use when registering architecture files in spec/design.yaml or drafting spec/design/*.md.
---


Operate within the **spectask** process defined in attached **spec/main.md**.

## `spec/design.yaml`

- **Schema:** top-level `schema: 1` and list **`documents`**. Each item has **`path`** and **`description`** (plain language: what the document covers, when to read it).
- **Paths:** repo-relative POSIX, typically `spec/design/{name}.md`. Reuse existing names when editing; avoid duplicates in `documents`.
- **Edits:** append or update entries when adding or renaming architecture markdown. Keep descriptions short and unique in intent (not copy-paste of the file title only).

## New or updated `spec/design/*.md`

1. **Purpose** — one paragraph: why this document exists.
2. **Scope** — in/out; link to HLA if this is a slice of the whole system.
3. **Content** — components, boundaries, data or control flow, integrations, constraints; diagrams as fenced blocks or links if the user prefers.
4. **Related** — other `spec/design` docs by path when relevant.

If the user only wants a registry row, still ensure the target **`.md` exists** or create a minimal stub so `path` is not orphaned.

## Spawn / agent reads

New paths are discoverable from **`spec/design.yaml`** once that file is read. For mandatory or default context at session start, paths still need **`globalRead` / `localRead`** (and non-empty **`description`**) in a Spawn extension **`config.yaml`** for the repo. If the user maintains this methodology pack, add a matching `files:` entry under **`extsrc/config.yaml`** and reinstall/update the extension; otherwise note the requirement for a companion extension or local config.


Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
