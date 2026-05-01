# Step 3: Design docs and authoring guides

## Goal
Align **spec/design** documentation with shipped hint behavior, maintainer editing rules for `navigation.yaml`, extension **`hints`** authoring, IDE render contract, and **`refresh_extension_for_ide`** calling **`refresh_navigation`**.

## Approach
Update the following files (expand sections only as needed — no new unrelated design files):

| File | Content to add or revise |
|------|---------------------------|
| `spec/design/hla.md` | Short subsection: hints flow (extension config → navigation mirror → skills + AGENTS); machine-owned **`- ext:`** vs maintainer **`rules`**. |
| `spec/design/agentic-flow.md` | Merged navigation, hint sources, skill **Hints** block placement, AGENTS warnings without truncation vs skill truncation. |
| `spec/design/user-guide.md` | Maintainers may hand-edit **`rules`** (and **`hint`** on **`read-required`** rows). **Do not** rely on manual edits under **`- ext:`** — Spawn overwrites those blocks on refresh. |
| `spec/design/extension-author-guide.md` | **`hints.global` / `hints.local`** in `config.yaml`; plain-text limits; interaction with merged `navigation.yaml`. |
| `spec/design/ide-adapters.md` | **`SkillMetadata.hints`**; rendered Markdown order (hints after body, before mandatory reads). |
| `spec/design/utility-method-flows.md` | **`refresh_extension_for_ide`** now includes **`refresh_navigation`**; pointer to ordering acceptance (skills before navigation in `_refresh_extension_core` if already documented). |

If a file lacks a suitable section, add a minimal subsection rather than rewriting the document.

## Affected files
- `spec/design/hla.md`
- `spec/design/agentic-flow.md`
- `spec/design/user-guide.md`
- `spec/design/extension-author-guide.md`
- `spec/design/ide-adapters.md`
- `spec/design/utility-method-flows.md`

## Notes
- Per **spec/main.md** Step 7, **`hla.md`** updates are mandatory when closing the task; this step collects the rest of design alignment in one pass.
- Keep prose in **English** per project rules for design docs.
