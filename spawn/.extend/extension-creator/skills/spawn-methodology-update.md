---
name: spawn-methodology-update
description: >-
  Update shipped methodology from a user instruction — clarify scope with
  questions, apply changes, validate the extension, bump version, and offer a
  git commit with a suggested message.
---

Goal: evolve an existing Spawn methodology pack from a concrete update request without guessing intent, and leave the pack check-clean and versioned.

## When to use

- User asks to update, revise, extend, or fix methodology content (specs under `extsrc/files/`, skills, reads, hints, MCP, setup).
- User gives a change brief for the pack and expects clarifying questions before edits.
- User wants a release-ready bump after methodology work (validate → version → optional commit).

## Prerequisites

- Extension repo with `extsrc/` and `extsrc/config.yaml`.
- Follow **`spawn-methodology-shape`** first if namespaces or static vs artifact layout are still undefined.
- Use sibling skills for the actual edits: **`spawn-ext-config`**, **`spawn-ext-skill-sources`**, **`spawn-ext-hints`**, **`spawn-ext-mcp`** as needed.

## Workflow

Copy and track:

```
Update progress:
- [ ] 1. Intake instruction
- [ ] 2. Scope questions → user answers
- [ ] 3. Apply changes
- [ ] 4. Validate
- [ ] 5. Increment version
- [ ] 6. Offer git commit
```

### 1. Intake

- Read the user’s update instruction as the source of truth for intent.
- Load pack context: `extsrc/config.yaml`, relevant `extsrc/files/**`, `extsrc/skills/*.md`, and (if present) `spawn/navigation.yaml`.
- Do **not** edit yet. Map the request to candidate surfaces: static specs, artifacts, skills, `config.yaml` reads/ignores/setup, hints, MCP.

### 2. Scope questions (required before edits)

Derive a **short** question set from gaps and risks — only what blocks a correct change. Prefer structured choices when the IDE supports them; otherwise ask conversationally.

Cover as needed (skip what the instruction already settles):

| Area | Ask when unclear |
|------|------------------|
| Target paths | Which namespaces / files / skills change? |
| Mode | `static` vs `artifact` for new or reclassified paths? |
| Reads | `globalRead` / `localRead` / skill `required-read` impact? |
| Compatibility | Patch (fix/clarify), minor (additive), or major (breaking remove/rename)? |
| Audience | Agent-facing procedure vs human guide vs both? |
| Out of scope | What must **not** change this pass? |

Rules:

- Ask once, then wait for answers. Do not start implementation mid-questionnaire.
- If answers conflict with the original instruction, restate the resolved plan in one short paragraph and confirm before editing.
- If the instruction is already complete and low-risk, ask **at most** one confirming question (or none) — do not invent busywork.

### 3. Apply changes

- Implement only the resolved plan.
- Keep skills thin; put long methodology in `extsrc/files/`.
- Every path under `extsrc/files/` must stay declared in `config.yaml`.
- Preserve stable extension **`name`**; do not rename skill ids or paths casually (breaking → major).
- Chat language: match the user. Spec/skill normative text: English unless the pack already uses another language.

### 4. Validate

From the extension source root:

1. Run **`spawn extension check . --strict`** (same bar as **`spawn-ext-verify`** step 1).
2. Fix failures and re-run until clean.
3. Optionally smoke-test install only if the user asked or the change touches install/materialization behavior.

Do **not** proceed to version bump while check fails.

### 5. Increment version (automatic)

After a clean check, bump **`version`** in `extsrc/config.yaml` using **`spawn-ext-increment-version`** — do not wait for a separate user request.

Choose level from the resolved plan:

- **PATCH** — clarifications, typo/docs fixes, non-breaking wording.
- **MINOR** — backward-compatible additions (new optional files/skills/reads).
- **MAJOR** — removals, renames, incompatible read/skill/template semantics.

State old → new version briefly after the edit. Re-run **`spawn extension check . --strict`** if the bump is the only remaining diff and check was already clean before the bump (quick confirm).

Exception: skip bump only when the user explicitly said the pass is draft/WIP and must not release — then note that version was left unchanged.

### 6. Offer git commit

After version bump:

1. Summarize what changed (paths + version).
2. Draft a commit message from the diff and resolved plan (why over file laundry list). Prefer conventional style when the repo already uses it, e.g. `feat(methodology): …` / `fix(methodology): …` / `docs(methodology): …`.
3. **Ask** whether to create the commit. Commit **only** if the user agrees.
4. If they agree, follow the repo’s git commit protocol (stage relevant files, commit with the agreed message, verify status). Never commit secrets (`.env`, credential files).

## Constraints

- No silent scope expansion beyond the answered plan.
- Do not commit unless the user accepts the offer (or separately asks to commit).
- Do not bump **`schema`** unless migrating Spawn config format.
- Do not add README or unrelated docs unless asked.
