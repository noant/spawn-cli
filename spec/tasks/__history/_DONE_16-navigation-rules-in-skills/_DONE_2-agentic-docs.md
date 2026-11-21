# 2: Agentic design doc sync

## Goal
Align documented agent flow with the new behavior so maintainers do not assume skills intentionally omit navigation `rules`.

## Approach
1. Edit `spec/design/agentic-flow.md` **Skill Flow** (and any adjacent sentence that says skills do not need to embed repo rules **because** navigation alone carries them): clarify that rendered skills **also** duplicate navigation-backed `rules` paths in mandatory/contextual lists for IDE visibility, while `spawn/navigation.yaml` remains the canonical index and entrypoint flow still applies.
2. Optionally add one sentence in `spec/design/data-structure.md` under navigation or rendered-metadata notes if a single cross-reference helps — only if it avoids contradicting the “generated outputs” story.

## Affected files
- `spec/design/agentic-flow.md`
- `spec/design/data-structure.md` (optional, minimal)

## Code examples
None.
