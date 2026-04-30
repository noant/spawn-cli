---
name: spectask-extend
description: Use when adding a new rule file under spec/extend/ (per spec/main.md).
---


Operate within the **spectask** process defined in attached **spec/main.md**.

Add `spec/extend/{name}.md` and obey **Folder Structure** rules.

New extend files only affect agents once they appear in **`spawn/navigation.yaml`** — that usually means declaring the path (and `globalRead` / `localRead`) in a Spawn extension’s **`config.yaml`** for this repo (e.g. extend the spectask pack or add a small companion extension), then reinstall/update extensions.

If the user does **not** say whether the new file should be **globally required** vs **context-only**, **ask**: should agents treat it as mandatory at session start (`globalRead: required`), optional global context (`globalRead: auto`), or only via skill/task-local reads (`localRead` / skill `required-read`)? Implement by adjusting extension `config.yaml` accordingly — there is no separate YAML registry under `spec/`.


Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
