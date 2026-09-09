# Spec-Tasks: AI-Oriented Development Methodology

## Folder Structure

- spec/main.md — this file.
- spec/design.yaml — index of architecture documents (`path` + `description` per entry); optional but recommended when multiple design files exist.
- spec/design/hla.md — project high-level architecture (required).
- spec/design/{name}.md — other architecture documents (optional; ADRs, notes, etc.); register in **spec/design.yaml** and declare as readable paths for agents — typically via a Spawn extension's `files:` (with appropriate reads) so they appear in `spawn/navigation.yaml`.
- spec/tasks/{task-code}-{slug}/ — task folder (artifact tree). `{task-code}` identifies the task (often a serial code; may instead be a key from an external tracker). `{slug}` is a short descriptive name.
- spec/tasks/{task-code}-{slug}/overview.md — task overview (required).
- spec/tasks/{task-code}-{slug}/{N}-{description}.md — subtask files (optional; required when `## Execution Scheme` defines 2+ steps).
- spec/seeds/{X}-{slug}.md — seed file (artifact tree in this methodology pack).

**Embedded rules:**

Every rule has a stable label `[R{n}-{slug}]`.

_Folder hygiene_

- **`R1-paths`**
  - under `spec/`, only paths allowed by the Folder Structure are permitted
  - no other files
- **`R2-no-clutter`**
  - do not create READMEs or other extraneous docs under `spec/`
  - special case of `R1-paths`

_Task identification_

- **`R3-code-num`**
  - for numeric `task-code`: suggest the next number (`R10-ask`)
  - wait for an explicit reply before creating `spec/tasks/{task-code}-{slug}/`
  - next number = highest existing `{task-code}` under `spec/tasks/` (including `_DONE_`) plus 1
- **`R4-code-tracker`**
  - a `task-code` from an external tracker must be the ticket key (e.g. `PROJ-123`)
  - segments after the first `-` may carry the slug

_Task specs_

- **`R5-new-task`**
  - new spec tasks follow Step 2 and the overview template at the end of this file
- **`R6-legacy-done`**
  - older `spec/tasks/_DONE_*` overviews may predate the current template
  - do not copy their structure unless it matches the template
- **`R7-process`**
  - status marks `[V]` and user prompts must reproduce the wording from the corresponding Step exactly
  - Steps run in order unless the process explicitly allows otherwise
- **`R8-concrete`**
  - specs are executable edits, not intentions
  - every overview and subtask names concrete paths and symbols (packages/modules, classes, methods, functions) under change
  - every Before / After pair in Code changes is a fenced minimal excerpt (real lines or the exact replacement) plus a behavior line
  - prose-only or "change X to Y" without code is invalid
- **`R9-greenfield`**
  - for new symbols, same Before/After discipline as `R8-concrete`, with two differences:
  - Before may be insertion-context only (nothing to quote)
  - After is still fenced code plus a behavior line

_Interaction and context_

- **`R10-ask`**
  - when you must ask the user (clarifications, confirmations, choices), **stop and request from the user**
  - do not continue the workflow until they answer
  - prefer the platform structured ask tool (see `R12-ask-tools`), multiple choice when possible
  - fallback order: platform tool -> **direct request to the user in your reply**
  - "Ask" / "request from the user" means only those channels
  - **never** treat asking as launching a Task / sub-agent / other agent; those tools are not ask tools
  - if no platform ask tool is available, stop, request from the user, then wait
  - do not ask when the answer is clear from context; ask only when the answer materially changes the next action
- **`R11-navigation`**
  - before drafting a spec, open **`spawn/navigation.yaml`**
  - read all `read-required`
  - read task-relevant `read-contextual`
  - apply them in the spec
  - if the file is absent, the rule is a no-op (proceed)
  - Spec self-review re-checks compliance; violations are defects
- **`R12-ask-tools`**
  - user-question tools by platform (data for `R10-ask` only):
  - **Cursor:** AskQuestion / cursor/ask_question
  - **VS Code/Copilot:** AskQuestions / vscode_askQuestions
  - **Claude Code:** AskUserQuestion
  - **Codex:** request_user_input
  - **Other:** IDE embedded ask tool; if none, stop and ask questions in the current chat (`R10-ask`)
- **`R13-model-line`**
  - every sub-agent prompt must include this line verbatim:
    > End your final response with the line `My model: X` where X is your actual model identifier (e.g. `claude-sonnet-4-6`, `gpt-4o`) — write your actual model identifier in place of X.
  - recording the model used by a sub-agent:
    - if the platform tool lets you pass an explicit sub-agent `model`, record that call parameter
    - if there is no model-selection parameter, read `My model:` from the sub-agent response and record that
  - who writes `Used model` / `[model-name]`: see `R15-done-marking`
- **`R14-changed-files`**
  - after finishing a create/edit batch, list every created or edited path (repo-relative, complete, no omissions)
  - renames and deletes count
  - applies to Step 1 (research), Step 2 (spec), Steps 5–6 (code), Step 8 (design), and any user-requested edits
  - **Propagation:** the executor sub-agent includes the full list in its final response
  - the coordinator (`A6-coordinator`) aggregates lists from child sub-agents and forwards the complete set to the user (and to its parent when the coordinator itself is a sub-agent)
  - do not drop or summarize away paths
- **`R15-done-marking`**
  - after a Coder (`A5-coder`) replies, the coordinator (`A6-coordinator`) marks the subtask done:
    - rename: `{N}-{description}.md` → `_DONE_{N}-{description}.md`
    - set: `Used model: {model}` from `R13-model-line`; `Suggested model` unchanged
  - only the coordinator (`A6-coordinator`) renames and writes `Used model` — the worker (`A5-coder`) must not
  - the worker sets `Status: Done` per Step 5 Coder protocol
  - mark immediately; do not defer
- **`R16-ambient`**
  - **Ambient context** is session/environment facts for sub-agents (repository name, session, and similar) — not coding conventions or task design rules
  - format when present: header `Ambient rules:` then one numbered item per line (`1) …`, `2) …`):
    ```
    Ambient rules:
    1) repository: {name}
    2) session: {id}
    ```
  - explicit empty: `Ambient context: none` — ambient **is** set; do **not** ask
  - if Ambient context is missing (neither an `Ambient rules:` block nor `Ambient context: none`), the agent **must** clarify via `R10-ask` before launching any sub-agent — mandatory
  - every sub-agent launch must put the resolved Ambient block at the start of the prompt per **Subagent run protocol**
  - each agent passes the block to child sub-agents unchanged

_Subagent governance_

- **`R17-classify`**
  - at the start of any spectask request, classify it as:
    - **[A] Question** — the user asks (wants an answer), not a "do" request
    - **[B] Initiative / task** — the user sets a task, an explicit "do", or asks to draft a spec
  - if unclear, ask via `R10-ask` and wait
  - [A] -> answer directly (light mode, no `spec/tasks/` artifacts); optionally launch `A2-researcher`/`A3-explorer` for read-only facts
  - [B] -> proceed to Step 1 (Research)
- **`R18-subagent-depth`**
  - limits subagent nesting — who may create whom:
  - `A1-drafter` — may launch `A2-researcher`, `A3-explorer`, `A4-reviewer`
  - `A2-researcher` — must not create subagents (works independently)
  - `A3-explorer` — may create only `A2-researcher`
  - `A4-reviewer` — may launch `A2-researcher` / `A3-explorer` (to verify findings); no deeper
  - `A5-coder` — must not create subagents (performs one subtask)
  - `A6-coordinator` — may launch `A5-coder` and `A4-reviewer`
  - violating this rule is a defect: a subagent that created a forbidden descendant must stop and return an error to the parent
- **`R19-no-ask-tool`**
  - subagents (`A2-researcher`, `A3-explorer`, `A4-reviewer`, `A5-coder`, `A6-coordinator`) are forbidden to ask questions via the ASK tool or any platform ask tool (AskQuestion, ask_question, AskUserQuestion, request_user_input, etc.)
  - a subagent asks questions only in text in its response to the parent
  - only the main chat (the agent coordinating the user, `A1-drafter` in current context) may use the ask tool for questions to the user
- **`R20-ask-if-unclear`**
  - a subagent may ask the parent a question if something in its task/direction is unclear
  - the question is asked only in text in the subagent's response (`R19-no-ask-tool`)
  - the subagent does not block indefinitely: if the answer is critical, it stops and returns the question to the parent; otherwise it proceeds with a stated assumption
- **`R21-navigate`**
  - after finishing a task/subtask, navigate the user to created/changed files via the platform navigate tool
  - navigate to each such file with a short description (chip label)
  - use line ranges (`from_line`/`to_line`) to point to the exact changed region when relevant
  - for git files pass the git session id; for ws docs omit it
  - never use navigate to read contents — only to show files in the UI

**Roles:**

Every role has a stable label `[A{n}-{slug}]`. Reference roles by label (e.g. `A1-drafter`), not by number — the label survives renumbering. One agent instance plays one role at a time.

- **`A1-drafter`** (Drafter)
  - main chat coordinator
  - researches the codebase alone or via `A2-researcher` / `A3-explorer`
  - writes the task specification (`overview.md`, subtasks, Execution Scheme)
  - owns Step 1 (Research) and Step 2 (Spec drafting); may also close Step 8 / Pattern extract in current context
- **`A2-researcher`** (Researcher)
  - general open-ended research (web, docs, codebase, hypothesis checking)
  - read-only except the research file
  - no subagents
- **`A3-explorer`** (Explorer)
  - coordinating researcher; decomposes research into sub-lines
  - may create only `A2-researcher`
  - supplies accurate Before / After context, paths, and symbols
- **`A4-reviewer`** (Reviewer)
  - reviews spec / code / research
  - reviews at Spec self-review (Step 3) and Code self-review (Step 6)
  - may launch `A2-researcher` / `A3-explorer`; no deeper
  - may fix defects found in that review; then stops and prompts the user
- **`A5-coder`** (Coder)
  - executes one Execution Scheme subtask
  - performs that subtask only (code, docs, config, rules); lists changed files per `R14-changed-files`
  - sets `Status: Done` in the subtask file; does not rename to `_DONE_` or write `Used model`
  - no subagents
- **`A6-coordinator`** (Coordinator)
  - coordinates Coders (`A5-coder`) per the Execution Scheme
  - owns Steps 5–6 end-to-end: launch Coders, `R15-done-marking`, launch Reviewer for Step 6
  - may launch `A5-coder` and `A4-reviewer`
  - must not be the same agent instance as `A1-drafter`

**Subagent run protocol**

Applies to every sub-agent launch for any role (`A2-researcher`, `A3-explorer`, `A4-reviewer`, `A5-coder`, `A6-coordinator`, and any further nesting).

1. Resolve Ambient context per `R16-ambient` (clarify if missing; do not ask when `Ambient context: none`).
2. Put the resolved Ambient block at the very start of the sub-agent prompt (verbatim `Ambient rules: …` or `Ambient context: none`).
3. Then add role-specific instructions (`R13-model-line`, `R14-changed-files`, Coder protocol, etc.).
4. Every agent that received Ambient context passes it to each child sub-agent unchanged — same wording, same order; do not drop, summarize, or rewrite.

---

## Process Overview

```
[0] Request classification (Question -> answer | Initiative -> Step 1)
→ [1] Research
→ [2] Spec drafting
→ [3] Spec self-review
→ [4] Spec review (user)
→ [5] Code implementation
→ [6] Code self-review
→ [7] Code review / debugging (user)
→ [8] Design document update
→ pattern extract to spawn/rules/
```

Mark each status [V] on completion. Prompt the user after steps 3, 6, and 7. Step 0 is a gate, not a status step — it has no status checkbox. After Step 8, run Pattern extract (not a Status checkbox).

---

## Step 0: Request classification

**Executor:** `A1-drafter` (current context)

0.1 Classify the request per `R17-classify`:
  - [A] Question -> answer directly (light mode); no `spec/tasks/` folder, no status checkboxes; optionally launch `A2-researcher`/`A3-explorer` (Subagent run protocol, `R13-model-line`) for accurate facts; if the answer reveals a real task, propose Step 2.
  - [B] Initiative / task -> proceed to Step 1 (Research).
0.2 If the type is unclear, ask via `R10-ask` and wait.

---

## Step 1: Research

**Executor:** `A1-drafter`

1.1 **Research depth selection** — ask the user (`R10-ask`) whether research is needed and at what depth:
  - [inline] — no subagents; the drafter researches in-chat (trivial, one-off questions)
  - [medium] — launch a single `A3-explorer` (or `A2-researcher` for a narrow single-line question) subagent (default)
  - [high] — launch several directed `A3-explorer` subagents, one per direction line
  - [skip] — no research needed; proceed directly to Step 2 (Spec drafting)
  Default to [medium] if the user does not specify. If the task is trivial and the implementation path is obvious, offer [skip] first.

1.2 **Research loop** — run research in a loop, up to 3 waves:
  1.2.1 Decompose — split research into independent direction lines (high = several, medium = one)
  1.2.2 Launch — launch `A3-explorer`/`A2-researcher` subagents, one per line (Subagent run protocol `R16-ambient`, `R13-model-line`)
  1.2.3 Collect — record findings into the `## Research summary` section of `overview.md`.
  1.2.4 Review — launch `A4-reviewer` to review the research (Subagent run protocol)
  1.2.5 Decide — gaps remain -> another wave (up to 3 total), return to 1.2.1; complete -> proceed to 1.3

1.3 **User research review** — show the research summary, ask the user (`R10-ask`):
  - [Proceed] — research sufficient, move to Step 2 (Spec drafting)
  - [Refine] — needs refinement, user points out what to clarify, return to 1.2 (another wave, up to 3)
  - [Stop] — stop here (finish or move to a separate chat with a prompt)

- set [V] "Research" `[model-name]` (record the model per `R13-model-line`): `- [V] Research [model-name]`
- list changed files per `R14-changed-files` if any files were edited

---

## Step 2: Spec drafting

**Executor:** `A1-drafter`

2.1 **Project rules (navigation)** — **MANDATORY!** Follow `R11-navigation` before writing any spec content.

2.2 **Implementation clarifications** — **MANDATORY!**:
- Before writing any spec content, identify ambiguous, optional, or convention-dependent aspects.
- Ask the user explicit questions (`R10-ask`) and wait for answers.
- Record answers (or agreed defaults) in **Details**.
- Skip only when there is a single obvious implementation path.
- If **Ambient context** is not already set in this chat, ask via `R10-ask` (repository, session, and similar); accept a list or explicit `Ambient context: none` (`R16-ambient`).
- If **motivation** is unclear, ask via `R10-ask` (multiple choice; adapt to context):
  - bug fix — restore correct behavior, regression, or broken promise
  - new feature — new user-visible capability, use case, or revenue path
  - UX — usability, accessibility, clarity, workflow friction
  - performance — speed, scale, or perceived responsiveness
  - refactor / tech debt — internal quality and maintainability, usually no user-visible change
  - security / compliance — vulnerability, regulatory obligation, data protection
  - reliability / ops — stability, observability, downtime, support burden
  - integration — external APIs, partners, cross-system workflow
  - experiment — hypothesis test or MVP slice
  - deprecation / migration — sunset or replace legacy behavior
  - other — name the driver in one sentence
- Put the chosen motivation in **`## Motivation`** (after **Goal**).
- Ask the user to choose an **invasiveness level** (`R10-ask`, multiple choice) — the edit scope the spec must respect:
  - **minimally-invasive** — edits confined to a single layer or library; all other layers/libraries are left untouched, even if the solution is a workaround (crutch).
  - **medium-invasive** — edits may span several adjacent layers or domains, e.g. backend + frontend, or domain1 + domain2.
  - **maximally-invasive** — edits may span all layers and all domains; the LLM follows the principle of deep rework over a superficial fix with compromises.
- Record the chosen level in **`## Invasiveness level`** (after **`## Motivation`**). Every affected file/symbol in the spec must stay within the chosen scope.

2.3 **Design overview**
- In the task `overview.md`, add a **Design overview** section:
  - affected modules
  - concrete paths and symbols (`R8-concrete`)
  - data flow changes
  - integration points
  
2.4 **Overview**
- `spec/tasks/{task-code}-{slug}/overview.md` follows the overview.md template
- sections through `## Details` (before/after and code examples go there)
- **Goal** = one sentence
- **Motivation** immediately after **Goal**
- add `## Execution Scheme` only when work splits into 2+ steps

2.5 **Execution Plan**
- when work has 2+ steps:
  - step ids in `## Execution Scheme` must match `{N}-{description}.md` filenames from 2.6
  - set `Suggested coordinator model` in the scheme

2.6 **Decomposition**
- create `{N}-{description}.md` per step with:
  - goal
  - approach
  - affected files (named classes/methods/functions per path)
  - code changes (before/after)
- set `Suggested model` for the step; leave `Used model` empty
- optional: launch `A3-explorer` (or `A2-researcher`) as a new sub-agent for read-only research / codebase analysis to determine accurate **Before** / **After** text, then merge findings into the step files (research / analysis only; `A1-drafter` owns decomposition and the spec); follow **Subagent run protocol** (`R16-ambient`)

- set [V] "Spec drafting" `[model-name]` (record the model per `R13-model-line`): `- [V] Spec drafting [model-name]`
- list changed files per `R14-changed-files`

---

## Step 3: Spec self-review

**Executor:** `A4-reviewer`

- sub-agent prompt: **Subagent run protocol** first (`R16-ambient`), then the line from `R13-model-line`
- review the spec for:
  - architectural impact, implementation errors, sequencing issues
  - concrete files, modules, and symbols (classes, methods, functions) per `R8-concrete` in every step and overview
  - compliance with `R11-navigation`
- fix if needed
- set [V] "Spec self-review" `[model-name]` (record the model per `R13-model-line`): `- [V] Spec self-review [model-name]`
- list changed files per `R14-changed-files` if any files were edited
- prompt: "Spec self-review complete — spec is ready for your review (Step 4). Reply 'spec review passed', 'lgtm', or 'ok' when satisfied."

---

## Step 4: Spec review

**Executor:** User

- on confirmation ("spec review passed", "lgtm", "ok"):
  - set [V] "Spec review"
  - prompt: "Reply 'implement' to start."

---

## Step 5: Code implementation

**Executor (coordination):** `A6-coordinator`
- **Same chat as Steps 1–3:**
  - `A1-drafter` must not act as `A6-coordinator` for Steps 5–6
  - on the implementation command, launch **one new sub-agent** as `A6-coordinator` for Steps 5–6 end-to-end
  - prefer `Suggested coordinator model` from `## Execution Scheme` (Task `model` when supported; else prompt + nearest slug)
  - parent waits for the coordinator, then waits for the user for Step 7
- **Fresh execute chat** (Steps 1–3 not in context): the current agent is `A6-coordinator`

**`A6-coordinator`** — follows the Execution Scheme, launches one `A5-coder` per step, then Step 6 (`A4-reviewer`).
**Each step in the Execution Scheme:** `A5-coder` (new sub-agent) — child of the coordinator.

- on "run it" / "implement" / "execute" / any direct instruction to start implementation:
  - if "Spec review" is not yet marked, set [V] "Spec review" automatically (implementation command implies approval)
  - if this chat already completed Steps 1–3 for the task:
    - launch the Steps 5–6 `A6-coordinator` sub-agent (see Executor above) and stop coordinating inline
    - prefer `Suggested coordinator model`
    - include in prompt: **Subagent run protocol** (`R16-ambient`); follow Steps 5–6 for `spec/tasks/{task-code}-{slug}/` as `A6-coordinator`; the line from `R13-model-line`
  - **MANDATORY!** launch an `A5-coder` sub-agent for each step — do NOT implement inline; no exceptions, even if a step seems trivial
    - prefer subtask `Suggested model`: pass as Task/sub-agent `model` when supported; else name in prompt and use nearest slug
    - Coder prompt must include: **Subagent run protocol** (`R16-ambient`), line from `R13-model-line`, changed-files list per `R14-changed-files`, **Coder protocol** below
  - follow the Execution Scheme: sequential (→), parallel (||)

- per subtask: after the Coder replies, mark done per `R15-done-marking` (rename + `Used model`)
- when all subtasks done and Step 6 complete: set [V] "Code implementation" `[model-name]` (coordinator model, per `R13-model-line`): `- [V] Code implementation [model-name]`
- forward the aggregated changed-files list to the user per `R14-changed-files`

**Coder protocol** (`A5-coder`, each Execution Scheme step):
- Implement the subtask; list changed files per `R14-changed-files`.
- At the end, set `Status: Done` in the subtask file.
- End the reply with the `My model:` line from `R13-model-line`.

---

## Step 6: Code self-review

**Executor:** `A4-reviewer` (new sub-agent; launched by `A6-coordinator`)

- sub-agent prompt: **Subagent run protocol** first (`R16-ambient`), then the line from `R13-model-line`
- review all changes: inconsistencies, naming, missing imports, broken contracts; respect Ambient context when present
- fix if needed
- set [V] "Code self-review" `[model-name]` (record the model per `R13-model-line`): `- [V] Code self-review [model-name]`
- list changed files per `R14-changed-files` if any files were edited
- prompt: "Self review done. Reply 'code review passed' to proceed."

---

## Step 7: Code review / debugging

**Executor:** User

- on confirmation ("code review passed", "lgtm", "ok"):
  - set [V] "Code review / debugging"
  - prompt: "Will now update design documents (Step 8)."

---

## Follow-up changes after implementation

If the user requests rework or fixes after Step 5:

- carry out the changes (as `A5-coder` or current context); list changed files per `R14-changed-files`
- ask via `R10-ask`: "Do you want to update the specifications of the current task?"
  - Yes: `A1-drafter` (or current context) edits the affected subtask files and/or `overview.md` to match the actual state; do not re-run the spec cycle; list changed files per `R14-changed-files`
  - No: proceed without changes

---

## Step 8: Design document update

**Executor:** `A1-drafter` (current context)

- do not start Step 8 until **Code review / debugging** is marked (Step 7)
- **Index** — read **spec/design.yaml**; if missing, only **spec/design/hla.md** applies (Folder Structure); add **spec/design.yaml** when you register more than one path under **spec/design/**
- **Scope** — from subtasks, the Execution Scheme, and the files changed/added in this task, choose the `path` rows to update; update those that matter, skip the rest
- **Write** — for each chosen path, align the markdown with the repo after this task; create the file if it is listed but missing
- if the task introduced or renamed architecture docs under **spec/design/**, update **spec/design.yaml** (`path` + `description` for each)
- rename the folder to _DONE_{task-code}-{name}
- if the Source seed Path in the overview is concrete and the listed spec/seeds file is linked to this overview, rename it once with _DONE_ added
- set [V] "Design document update" — fill the model name in brackets: `- [V] Design document update [model-name]`
- list changed files per `R14-changed-files`
- continue with **Pattern extract** below (same run when closing via Steps 7–8)

---

## Pattern extract (after Step 8)

**Executor:** `A1-drafter` (current context)

After Step 8, extract reusable approaches into **`spawn/rules/`** as project-standard candidates. Skill: **spectask-extract-patterns**.

The agent filters candidates, presents the final list to the user in this run, then asks per-candidate acceptance via the ask tool (`R10-ask`).

**Order (mandatory):**

1. **Discover** — find and filter reusable candidates (agent only).
2. **Present** — show the filtered list to the user in one message right after Step 8 (title + one-line rationale + suggested scope per survivor).
3. **Ask** — ask per-candidate acceptance via the ask tool (`R10-ask`); wait for the user's answer.
4. **Write** — only candidates the user accepted as Required or Optional.

This step always runs after Step 8. If Discover leaves zero candidates, say so briefly and stop.

### Discover (before presenting)

- review this task's changes, subtasks, Execution Scheme, and relevant codebase for reusable patterns
- apply **Selection criteria** below; reject junk immediately
- if zero candidates remain: say so briefly and stop — do not present; do not invent fillers

### Selection criteria

Propose only candidates that pass all of:

- **Reusable** — useful beyond this single task
- **Actionable** — can become a short rule an agent can follow
- **Standard candidate** — plausible as a lasting convention
- **Not already covered** — check **`spawn/rules/`**, **`spawn/navigation.yaml`**, and related Spawn reads for duplicates
- **Pre-existing code OK** — a pattern already in the codebase but not yet in rules remains valid
- **Code examples** — prefer short real excerpts; prose-only when necessary

Reject immediately (do not offer):

- task-specific wiring, ticket ids, temporary workarounds
- restatements of HLA, language defaults, or existing rules
- vague slogans without an enforceable rule
- low-value or speculative ideas (junk)

### Present (after Discover)

- run only when Discover left one or more candidates
- present the entire list in **one message**, right after Step 8
- for each survivor: short title, one-line rationale, suggested scope (Required = `read-required`, Optional = `read-contextual`)
- then ask via the ask tool (`R10-ask`): per-candidate Required/Optional/Decline, plus a "decline all" option
- then wait — do not write rules, do not run `spawn refresh`, do not start the next task

### Apply the user's answer (after the ask)

- write only Required/Optional candidates
- if all Declined (or "decline all"): write nothing
- candidates not addressed default to **Decline** (do not invent consent)

### Write

1. Write under **`spawn/rules/`** (create the folder if missing).
2. Prefer an existing **`spawn/rules/`** file on the same topic — merge or revise. If none fits, create a new kebab-case Markdown file.
3. Prefer short code examples in each rule when applicable (criterion 6).
4. Add each file to **`spawn/navigation.yaml`** under **`read-required` → `rules`** or **`read-contextual` → `rules`** as the user chose. Row: **`path`** + short **`description`**. Never list the same path in both.
5. Run exactly **`spawn refresh`** in the terminal.

---

## overview.md Template

```markdown
# {task-code}: {Title}

## Source seed
- Path: {seed path or none}

## Status
- [ ] Research [model]
- [ ] User research review
- [ ] Spec drafting [model]
- [ ] Spec self-review [model]
- [ ] Spec review
- [ ] Code implementation [model]
- [ ] Code self-review [model]
- [ ] Code review / debugging
- [ ] Design document update [model]

## Goal
{One concise sentence.}

## Motivation
{Why this change — from the user request, or from the clarification answer.}

## Invasiveness level
{minimally-invasive | medium-invasive | maximally-invasive — chosen in Step 2.2; constrains the edit scope of the spec.}

## Research summary
{Synthesized research findings with links to research files. Present only when the research phase (Step 1) ran.}

## Design overview
- Affected modules: {list}
- Files & symbols (concrete paths; class / method / function / module names to touch): {list}
- Data flow changes: {description}
- Integration points: {list}

## Before → After
### Before
- {current state}
### After
- {desired state}

## Details
{Clarifying details, code examples, constraints.}

## Execution Scheme
Suggested coordinator model: {model}
> Each step id is the subtask filename (e.g. `1-abstractions`).
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step {N}-{description} → step {N}-{description}
- Phase 2 (parallel):   step {N}-{description} || step {N}-{description}
- Phase 3 (sequential): step review — inspect all changes, fix inconsistencies
```

Omit `## Execution Scheme` if there is no decomposition (single-file spec).

---

## Subtask file template

Filename must match the step id from `## Execution Scheme` (e.g. `1-abstractions.md`). One file per step.

````markdown
# Step {N}: {Short title}

Status: Not implemented
Suggested model: {model}
Used model:

## Goal
{One sentence — outcome of this step.}

## Approach
{Order of work, constraints, references to spec/design if needed.}

## Affected files
- `{path/relative/to/repo/root}`
- `{...}` — {...}

## Code changes (before / after)

### `{path/to/file.ext}` — {path plus named symbols (module, class, method, or function) + what changes}

**Before**
```code
{concrete minimal excerpt or exact lines, not vague prose}
```
{what this code does — behavior, not a repeat of the diff}

**After**
```code
{replacement or new block — one-to-one with Before when editing existing text}
```
{what the new code does — behavior, not a repeat of the diff}

### `{path/to/other.ext}` — {where}
**Before**
```code
{concrete minimal excerpt or exact lines, not vague prose}
```
{what this code does — behavior, not a repeat of the diff}
**After**
```code
{replacement or new block — one-to-one with Before when editing existing text}
```
{what the new code does — behavior, not a repeat of the diff}

## Additional actions
{Optional: shell commands, manual verification steps, follow-up tasks, or other non–file-edit work for this step.}
````

---

**Seed** — optional: a Markdown file in `spec/seeds/` to capture an idea fast; Steps 1–8 do not require it unless you deliberately start there. Link from `overview.md` when you promote into a spectask; apply Step 8 item 6 when closing the linked seed.

## Seed file template (header)

```markdown
linked task: {task path or none}

{idea content}
```

---

## HLA Template

`spec/design/hla.md` describes the project high-level architecture and interaction of abstractions. It is the single source of truth for how components, services, and implementations relate to each other.

```markdown
# High-Level Architecture (HLA)

This document describes the high-level architecture and interaction of abstractions in the project.

## Project Overview

- Technologies: {list of core technologies}
- Infrastructure services: {list of infrastructure services, e.g. DB, message broker, cache}
- Frameworks: {list of frameworks and major libraries}

## Entry Points

### {Entry point name} (Frontend / UI / Console / CLI / Worker)

- Used API / service entrypoints: {list of service or API endpoints this entry point calls}

## Services & API Endpoints

### {Service or API endpoint}

- Used service abstractions: {list of interfaces/abstractions consumed}
- Used concrete implementations: {list of concrete implementations wired to the abstractions}

## Service Implementations

### {Service implementation}

- Used service abstractions: {list of interfaces/abstractions consumed}
- Used concrete implementations: {list of concrete implementations wired to the abstractions}

## Data Flow

{description of how data flows through the system: entry points → services → implementations → infrastructure}
```
