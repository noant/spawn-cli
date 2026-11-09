---
name: spectask-shake-out
description: Spec shake-out — cross-model panel review of spec subtasks, synthesized fixes with git-diff fix review, final full-spec panel review.
---


Spec review variant of **spectask-execute-step-by-step-dual-review** for SPECS ONLY: no code is written.
Mandatory: read **spec/main.md** in full (subtask structure, Coder protocol, Subagent run protocol).

**Role:** `A6-coordinator`

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`, `R23-review-scheme`

**Roles involved:**
- `A6-coordinator`
- `A5-coder` (spec fixer)
- `A4-reviewer` (panel xN per subtask)
- `A4-reviewer` (fix review)
- `A4-reviewer` (final full-spec panel xN)

## Step 0 - one-time setup

Ask ONCE (`R10-ask`), all questions in a single call, before the first subtask:

1. Detect the models actually available on THIS agent. Do NOT hardcode names.
2. Offer at least 6, preferably 9, numbered panel variants:
   - 1-3 models per panel, prefer different families;
   - single-model panel only if fewer than 2 families are available;
   - list each member with role names, e.g. `#1: sonnet-5 + Kimi-k3.1-pro (panel members #1-#2)`;
   - if not enough variants can be built, say so and offer what exists.
3. Offer in the same call:
   - coder model (spec fixer);
   - fix-reviewer model (`A4-reviewer`);
   - fallback per panel member (or one common fallback); default: nearest model of another family.
4. Wait interval between subtasks: none / 30s / 1m / 5m / 30m / 45m / 1h.
5. End-of-work action: commit / commit and push / nothing (report only).

Record all choices in `## Review models` in the review-findings file.
Do NOT re-ask. Intermediate questions ONLY for conceptual problems.

## Per-subtask loop (each Execution Scheme subtask, in scheme order)

1. Panel review:
   - launch N `A4-reviewer` subagents IN PARALLEL (chosen models; unavailable model -> its fallback, record it);
   - REVIEW-ONLY: no edits;
   - prompt must state the role name, e.g. `Role: A4-reviewer (panel member #k, model X)`;
   - each reviewer gets: authoritative spec files, the subtask, verdict format, `My model:` line (`R13`);
   - verdicts: `OK` / `SPEC_FINDINGS` (local: ambiguity, gaps, contradictions) / `CONCEPTUAL_PROBLEM` (spec-level flaw, cross-subtask breakage);
   - all `OK` -> go to step 2.
2. Synthesize:
   - merge findings into ONE consolidated fix list;
   - deduplicate, drop disagreed nitpicks;
   - keep agreed issues, each with a clear resolution.
3. Apply fixes:
   - launch ONE `A5-coder` subagent (coder model; prompt states `Role: A5-coder (spec fixer, model X)`);
   - apply the fix list to spec files ONLY (subtask, overview, scheme as needed);
   - coder lists changed files (`R14`);
   - spec must stay re-runnable from scratch and template-conformant.
4. Fix review:
   - launch ONE `A4-reviewer` subagent (fix-reviewer model; prompt states `Role: A4-reviewer (fix reviewer, model X)`);
   - read the PREVIOUS version of each changed file via git (diff/show);
   - verify every accepted finding is resolved;
   - search for NEW problems introduced by the fixes;
   - `PASS` -> step 5; `FINDINGS` -> repeat steps 2-4.
5. Mark done per `R15-done-marking`; record the round in the review-findings file and overview `## Details` (found / decided / changed).
6. Conceptual problem (critical): STOP. Ask (`R10-ask`):
   - a) fix the spec (panel + coder, then re-review);
   - b) user handles it;
   - c) abort shake-out.
   This is the ONLY allowed mid-run user interaction (plus the wait interval).
7. If a wait interval was chosen, wait before the next subtask.

## Final full-spec cross review

1. Run the SAME panel over the WHOLE spec (all subtasks + overview + scheme).
2. Synthesize findings, apply via the coder, fix-review via the fix-reviewer (git diff against pre-final state).
3. Repeat until `PASS`.
4. Perform the Step 0 end-of-work action.
5. Report: rounds per subtask, findings, models used (including fallback substitutions).

**Notes:**
- Only spec files are modified; never code.
- Spec corrections must keep the task re-runnable from scratch and template-conformant (spec/main.md).
- Every subagent prompt states: role name, authoritative spec files, round-specific findings, verdict format, `My model:` line (`R13`).
- Fallback substitutions are always recorded, never silent.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/rules/01-vacancy-cleanup-subtrees.md` - finalize_*_repo cleanup must know every adapter-written config subtree; avoid dead configs.
- `spawn/rules/02-agent-config-namespacing.md` - Local rule file.
- `spawn/rules/03-adapter-spawn-warning.md` - IDE adapters emit warnings via SpawnWarning category for friendly CLI output.
- `spawn/rules/04-adapter-skill-name-constraints.md` - Local rule file.
- `spawn/rules/05-adapter-canonical-config-file.md` - Local rule file.
- `spawn/rules/06-new-ide-adapter-checklist.md` - Local rule file.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
