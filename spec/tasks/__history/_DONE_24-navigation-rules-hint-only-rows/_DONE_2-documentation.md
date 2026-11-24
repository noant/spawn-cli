# Step 2: User-facing and design documentation

## Goal
Document hint-only **`rules`** rows so maintainers know they are supported under **`read-required`**, how they differ from file-backed rows, and that **`spawn refresh`** / **`spawn rules refresh`** preserve them.

## Approach

1. **`README.md`** — section **Hints in `spawn/navigation.yaml`** (or adjacent **How to add rules** subsection):
   - State that under **`read-required` → `rules`**, a row may be either:
     - **`path`** (+ **`description`**, optional **`hint`**) pointing at **`spawn/rules/...`**, or
     - **`hint`** only (standalone reminder; does not add a mandatory read).
   - Clarify invalid paths: if **`path`** names a **`spawn/rules/...`** file that does **not** exist after refresh, that row is **dropped entirely** (**`hint`** is **not** kept as hint-only — fix or remove **`path`** first).
   - Note ordering: hints from **`rules`** list order feed AGENTS/skills rollup together with extension **`hints.global`** per existing dedupe rules.
   - Remind that **`read-contextual` → `rules`** hints remain **not** rolled into AGENTS/skills (task 18).

2. **`spec/design/agentic-flow.md`** — navigation merge / maintainer hints paragraph:
   - Mention hint-only **`rules`** rows under **`read-required`** as a first-class maintainer option.

3. **`spec/design/user-guide.md`** — maintainer editing **`spawn/navigation.yaml`**:
   - Align short prose with README so behavior is consistent.

## Affected files (expected)

- **`README.md`**
- **`spec/design/agentic-flow.md`**
- **`spec/design/user-guide.md`**

## Non-goals

- Rewriting full extension-author guides unless a single cross-reference sentence is needed for consistency.
