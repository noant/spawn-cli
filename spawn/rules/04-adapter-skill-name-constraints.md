# Rule: adapter-specific skill-name constraints

Optional. For IDE adapters whose agent enforces stricter skill-name rules than
the spawn-wide `normalize_skill_name` (which keeps `[a-z0-9._-]`).

Conventions:

1. After `normalize_skill_name`, apply adapter-specific sanitization:
   - replace `.` and `_` with `-`
   - collapse repeated `-`, strip leading/trailing `-`
   - enforce the agent's regex (e.g. OpenCode `^[a-z0-9]+(-[a-z0-9]+)*$`, 1-64 chars)
2. Enforce `frontmatter name == rendered directory name` when the agent requires
   it (precedents: `cline.py`, `opencode.py`):

```python
name = re.sub(r"-{2,}", "-", normalize_skill_name(skill.name)
              .replace("_", "-").replace(".", "-")).strip("-")
rendered = render_skill_md(skill.model_copy(update={"name": name}))
```

3. Do not change `normalize_skill_name` globally for one adapter's constraint;
   sanitize inside the adapter only.
