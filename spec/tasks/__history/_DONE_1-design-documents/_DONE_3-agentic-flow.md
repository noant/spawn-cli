# 3-agentic-flow

## Goal
Create `spec/design/agentic-flow.md` describing how files, skills, navigation, and rendered instructions interact during AI-assisted development.

## Approach
- Define the agent startup and task flow around `spawn/navigation.yaml`.
- Explain required global reads, contextual global reads, extension-local required reads, extension-local contextual reads, and skill-specific `required-read` overrides.
- Describe how `generate-skills-metadata(extension)` combines raw skill frontmatter/config metadata, content, required reads, and auto reads.
- Describe rendered skills for IDEs: name, description, body content, mandatory file reads, contextual file reads, and the instruction to consult `spawn/navigation.yaml` for additional context.
- Explain how rendered skills and navigation create one coherent AIDD experience across IDEs and extensions.
- Explain how `spawn/rules/` contributes user-authored local rules to navigation.
- Clarify that `spawn/.extend/{ext}` is ignored by agents while rendered skills and navigation are the intended agent-facing surfaces.

## Affected files
- `spec/design/agentic-flow.md`
- `spec/navigation.yaml`

## Code examples
Use compact examples of rendered skill sections and navigation snippets.
