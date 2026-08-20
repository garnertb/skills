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

## Command-Like Skills

A skill that contains a `references/routing.md` is a **command-like skill**: its
`SKILL.md` is an entry point that dispatches to nested commands rather than
executing a single workflow. Treat these skills like a CLI:

- The `SKILL.md` defines the top-level command (e.g. `/skill-name`) and
  delegates to `references/routing.md` to decide which nested command applies.
- `references/routing.md` maps user intent to a nested command and MUST NOT
  auto-run a command — it recommends, and the user confirms.
- Each nested command (e.g. `report`, `plan`, `config`) has its own reference
  doc under `references/` that the entry point loads on demand.

See [skills/dependabot/SKILL.md](../skills/dependabot/SKILL.md) and its
[reference/routing.md](../skills/dependabot/reference/routing.md) for a working
example.

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

## Modifying a Skill

When you change any skill under `skills/` (its `SKILL.md`, `reference/`,
`scripts/`, assets, or `evals/`), two steps are part of the change — not
afterthoughts:

### 1. Bump the skill version

Every `SKILL.md` has a `metadata.version` field (e.g. `version: "1.1"`). Bump it
based on the nature of the change:

- **Patch** (`1.1` → `1.1.1`): typo, wording, formatting, or non-behavioral
  clarification.
- **Minor** (`1.1` → `1.2`): new but backward-compatible behavior — a new
  command, guardrail, reference section, or expanded coverage.
- **Major** (`1.1` → `2.0`): breaking or incompatible change — removed/renamed
  commands, changed output contract, or reworked routing.

If a skill has no `metadata.version`, add one starting at `"1.0"`. Never ship a
behavioral change without moving the version.

### 2. Cover behavior changes with an eval (if the skill has `evals/`)

When the change alters observable agent behavior (routing, output shape, new
guardrails, new commands, corrected mistakes) and the skill has an `evals/`
folder:

- **Check existing coverage** in the skill's `evals/evals.json` and fixtures.
- **Add or update an eval** with a unique `id`, a realistic `prompt`, and an
  `expected_output` that describes the desired behavior in terms a grader can
  check — or update an existing `expected_output` when a requirement changed.
- **Add fixtures** under `evals/fixtures/` when the eval needs a reference
  output, following the existing naming (e.g. `eval-<id>-good.md`).

Always state in your summary the version change (old → new) and whether you
added, updated, or intentionally skipped an eval — and why.

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
