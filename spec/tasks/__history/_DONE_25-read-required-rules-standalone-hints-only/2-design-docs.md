# Step 2: Design documentation alignment

## Goal
Update published design text so authors no longer expect **`hint`** on file-backed **`read-required` → `rules`** rows.

## Approach
1. **`spec/design/agentic-flow.md`**: In the navigation / hints section and YAML example, remove **`hint`** from file-backed **`rules`** examples; show reminders as **hint-only** rows and/or **`- ext:` → `hints`**. State clearly that maintainer rollup uses **only** standalone hint-only rows under **`read-required` → `rules`** (plus extension hints), not **`hint`** beside **`path`**.
2. **`spec/design/user-guide.md`**: Adjust the maintainer hand-edit bullet that mentions optional **`hint`** on path rows so it matches the new rule (path row: **`path`** + **`description`** only; reminders: separate rows).
3. **`README.md`**: If it documents `navigation.yaml` **`rules`** with **`hint`** on the same line as **`path`**, update to the standalone pattern; skip if there is no such snippet.

## Affected files
- `spec/design/agentic-flow.md`
- `spec/design/user-guide.md`
- `README.md` (conditional)
