# Copilot Instructions

This repository is a collection of AI
[skills](https://agentskills.io/what-are-skills) — portable, structured
knowledge modules that extend AI agent capabilities.

## Project Structure

```
skills/
├── <skill-name>/
│   ├── SKILL.md        # Required: instructions + YAML frontmatter metadata
│   ├── references/     # Optional: detailed documentation (REFERENCE.md)
│   ├── scripts/        # Optional: executable code
│   └── assets/         # Optional: templates, resources
```

## Skill File Format

Every `SKILL.md` must include YAML frontmatter with at minimum:

```yaml
---
name: skill-name # kebab-case, matches folder name
description: Brief description of what this skill does.
metadata: # Optional
  author: username
  version: "1.0"
---
```

The body contains actionable instructions for AI agents. Use MUST/SHOULD/NEVER
language for clear guidance. See
[skills/shell-script-generator/SKILL.md](../skills/shell-script-generator/SKILL.md)
for a well-structured example.

## Development Workflow

### Creating a New Skill

Use the VS Code task "Create New Skill" or run:

```bash
mkdir -p ./skills/<skill-name> && curl -sL https://raw.githubusercontent.com/anthropics/skills/main/template/SKILL.md -o ./skills/<skill-name>/SKILL.md
```

### Validation

Skills are validated against the
[agentskills specification](https://agentskills.io/specification) using the
`skills-ref` validator:

```bash
./scripts/validate-skills              # Validate all skills
./scripts/validate-skills <skill-name> # Validate specific skill
```

Requires `uvx` (from [uv](https://docs.astral.sh/uv/)).

### Formatting

Markdown files use Prettier with prose wrap at 80 characters:

```bash
pnpm format         # Format all skill markdown files
pnpm format:check   # Check formatting without modifying
```

## CI Quality Gates

All PRs run two checks via `.github/workflows/quality.yml`:

1. **Skill validation** — `./scripts/validate-skills` must pass
2. **Format check** — `pnpm format:check` must pass

## Key Conventions

- Skill folder names use **kebab-case** matching the `name` in frontmatter
- Use `references/REFERENCE.md` for detailed examples and extended documentation
- Keep `SKILL.md` concise and actionable; put verbose content in references
- Shell scripts in this repo follow the patterns in
  [shell-script-generator](../skills/shell-script-generator/SKILL.md)
