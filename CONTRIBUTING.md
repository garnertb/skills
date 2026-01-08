# Contributing to Skills

Thank you for your interest in contributing to this collection of AI skills!
This guide will help you get started.

## What Are Skills?

Skills are portable, structured knowledge modules that extend AI agent
capabilities. Each skill is a folder containing a `SKILL.md` file with metadata
and instructions, optionally bundled with scripts, templates, and reference
materials.

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (for formatting)
- [pnpm](https://pnpm.io/) (package manager)
- [uv](https://docs.astral.sh/uv/) (for skill validation via `uvx`)

### Setup

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   pnpm install
   ```

## Creating a New Skill

### Using the VS Code Task

If you're using VS Code, run the **Create New Skill** task from the Command
Palette (`Cmd+Shift+P` → `Tasks: Run Task` → `Create New Skill`).

### Manual Creation

```bash
mkdir -p ./skills/<skill-name>
curl -sL https://raw.githubusercontent.com/anthropics/skills/main/template/SKILL.md \
  -o ./skills/<skill-name>/SKILL.md
```

### Skill Structure

```
skills/
├── <skill-name>/
│   ├── SKILL.md        # Required: instructions + YAML frontmatter
│   ├── references/     # Optional: detailed documentation (REFERENCE.md)
│   ├── scripts/        # Optional: executable code
│   └── assets/         # Optional: templates, resources
```

### SKILL.md Format

Every `SKILL.md` must include YAML frontmatter:

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
language for clear guidance.

## Development Workflow

### Validation

Skills are validated against the
[agentskills specification](https://agentskills.io/specification):

```bash
# Validate all skills
./scripts/validate-skills

# Validate a specific skill
./scripts/validate-skills <skill-name>
```

### Formatting

Markdown files use Prettier with prose wrap at 80 characters:

```bash
# Format all skill markdown files
pnpm format

# Check formatting without modifying
pnpm format:check
```

## Submitting Changes

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the conventions below
3. Run validation and formatting checks:
   ```bash
   ./scripts/validate-skills
   pnpm format:check
   ```
4. Commit your changes with a clear, descriptive message
5. Open a pull request against `main`

### CI Quality Gates

All PRs must pass these checks:

1. **Skill validation** — `./scripts/validate-skills` must pass
2. **Format check** — `pnpm format:check` must pass

## Conventions

### Naming

- Skill folder names use **kebab-case** matching the `name` in frontmatter
- Example: `shell-script-generator/` with `name: shell-script-generator`

### Documentation

- Keep `SKILL.md` concise and actionable
- Use `references/REFERENCE.md` for detailed examples and extended documentation
- Shell scripts should follow patterns in the
  [shell-script-generator](skills/shell-script-generator/SKILL.md) skill

### Code Style

- Use hard tabs in shell scripts
- Follow the shell script best practices defined in
  [shell-script-generator](skills/shell-script-generator/SKILL.md)

## Questions?

If you have questions or need help, feel free to open an issue for discussion.
