---
name: authoring-skills
description: >
  Write, review, and refine agent skills (SKILL.md files) that an AI agent can
  reliably discover and use. Use when creating a new skill, improving an
  existing one, writing or fixing a skill description, deciding how to split
  content across reference files, or debugging why a skill is not triggering.
metadata:
  author: garnertb
  version: "1.0"
---

# Authoring Skills

Write skills that are concise, discoverable, and tested. A skill is a `SKILL.md`
file (plus optional bundled files) that an agent loads on demand to extend its
capabilities. These are the practices that make one effective.

## Core principles

- **Be concise.** The agent is already capable; add only context it lacks.
  Challenge every sentence: "Does the agent really need this?" Once `SKILL.md`
  loads, every token competes with the rest of the context window. Cut
  explanations of things the agent already knows.
- **Match freedom to fragility.** Give specific, low-freedom instructions (exact
  commands, "run this script, do not modify it") for fragile, error-prone, or
  order-dependent operations. Give high-freedom direction (general heuristics,
  numbered guidance) when many approaches are valid and context decides.
- **Test across every model you target.** A skill augments a model, so its
  effectiveness depends on that model. What a strong reasoning model follows
  with terse instructions may need more detail for a smaller one.

## Frontmatter

Every `SKILL.md` MUST begin with YAML frontmatter containing `name` and
`description`:

- `name`: lowercase letters, numbers, and hyphens only; max 64 characters; no
  XML tags; no reserved words (`anthropic`, `claude`). MUST match the folder
  name.
- `description`: non-empty; max 1,024 characters.

### Naming

Use the **gerund form** (verb + -ing) to name the activity: `processing-pdfs`,
`analyzing-spreadsheets`, `authoring-skills`. Noun phrases (`pdf-processing`)
are acceptable. NEVER use vague names (`helper`, `utils`, `tools`) or overly
generic ones (`documents`, `data`, `files`). Keep naming patterns consistent
across a skill collection.

### Writing the description

The description is the single most important field for discovery — the agent
reads it to decide whether to load the skill from among many.

- Write in the **third person**. "Extracts text from PDFs" — NEVER "I can help
  you..." or "You can use this to...".
- State **both what it does and when to use it**, including concrete trigger
  terms the user is likely to say.
- Be specific. "Analyze Excel spreadsheets, create pivot tables, generate
  charts. Use when working with .xlsx files or tabular data." NOT "Helps with
  documents."

## Progressive disclosure

The agent loads only what it needs: metadata first, then `SKILL.md`, then
reference files on demand. Structure for that.

- Keep the `SKILL.md` body **under 500 lines**. Split overflow into separate
  files.
- Keep references **one level deep** from `SKILL.md`. The agent may only preview
  (not fully read) files that are referenced from other referenced files, so
  NEVER nest references more than one hop.
- Give files **descriptive names** (`form_validation_rules.md`, not `doc2.md`)
  and organize by domain (`reference/finance.md`, `reference/sales.md`).
- For any reference file longer than ~100 lines, add a **table of contents** at
  the top so the agent sees the full scope even from a partial read.
- Bundle comprehensive resources freely (full API docs, large datasets,
  extensive examples) — they cost no context tokens until read.

**Patterns:**

- _High-level guide with references_ — `SKILL.md` holds quick-start content and
  links to `FORMS.md`, `REFERENCE.md`, `EXAMPLES.md` for advanced topics.
- _Domain-specific organization_ — one reference file per domain so the agent
  loads only the relevant one.
- _Conditional details_ — show the common path inline, link to edge cases.

## Workflows and feedback loops

- For complex, multi-step tasks, break the work into clear sequential steps.
  Provide a **checklist** the agent can copy into its response and check off.
- Build **feedback loops**: run a validator, fix errors, repeat. The "validator"
  can be a script (`python scripts/validate.py`) or a reference doc the agent
  compares against. Tell the agent to proceed only once checks pass.
- For large or branching workflows, push the detail into a separate file and
  tell the agent to read it based on the task at hand.

## Content guidelines

- **No time-sensitive information.** NEVER write "before August 2025, use the
  old API." Put deprecated guidance in a clearly labeled "Old patterns" section
  instead.
- **Consistent terminology.** Pick one term and use it throughout — always
  "field", not a mix of "field", "box", "element", "control". Consistency helps
  the agent parse instructions.
- **Concrete examples over abstract description.** For output-quality tasks,
  show input/output pairs; they convey style and detail better than prose.

## Common patterns

- **Template pattern** — provide an output template. Use "ALWAYS use this exact
  template" for strict formats; offer "a sensible default, use judgment" for
  flexible ones.
- **Examples pattern** — supply labeled input → output examples for tasks where
  quality depends on seeing the desired style.
- **Conditional workflow pattern** — route the agent through decision points
  ("Creating new content? → follow X. Editing? → follow Y.").

## Evaluation and iteration

- **Build evaluations first.** Before writing extensive docs: run the agent on
  representative tasks _without_ the skill, document the failures, create at
  least three evaluation scenarios targeting those gaps, establish a baseline,
  then write the minimal instructions needed to pass. This solves real problems
  instead of imagined ones.
- **Iterate with two roles.** Use one agent instance to author and refine the
  skill, and a fresh instance (skill loaded) to perform real tasks. Observe
  where the fresh instance struggles and bring specifics back to refine the
  skill.
- **Watch how the agent navigates.** Unexpected read order, missed references,
  or ignored files signal structural problems. The `name` and `description`
  matter most for triggering — tune them when the skill fails to activate.

## Anti-patterns to avoid

- NEVER use Windows-style backslash paths; always forward slashes
  (`scripts/helper.py`).
- Do not offer many competing options. Give one default with an escape hatch:
  "Use pdfplumber for text; for scanned PDFs use pdf2image with pytesseract."
- Do not pad `SKILL.md` with explanations of concepts the agent already
  understands.

## Skills with executable code

When a skill bundles scripts:

- **Solve, don't defer.** Scripts MUST handle their own error conditions (create
  a missing file, fall back on a permission error) rather than failing and
  leaving the agent to improvise.
- **No voodoo constants.** Justify and document every configuration value with a
  comment. If you cannot explain why a timeout is 30s, the agent cannot either.
- **Prefer utility scripts** for deterministic work — they are more reliable,
  cheaper in tokens, and more consistent than regenerated code.
- **Make execution intent explicit:** "Run `analyze_form.py` to extract fields"
  (execute) vs. "See `analyze_form.py` for the algorithm" (read as reference).
- **Do not assume packages are installed.** State required packages and install
  commands; verify they are available in the target runtime.
- **Reference MCP tools by fully qualified name** (`ServerName:tool_name`) to
  avoid "tool not found" errors.
- For high-stakes or batch operations, create a **verifiable intermediate
  output** (a plan file) and validate it with a script before executing.

## Checklist

Before sharing a skill, verify:

- [ ] Description is specific, third-person, and states what it does AND when to
      use it
- [ ] `name` is kebab-case, matches the folder, and uses gerund form
- [ ] `SKILL.md` body is under 500 lines; overflow is in separate files
- [ ] File references are one level deep; long reference files have a table of
      contents
- [ ] No time-sensitive information; terminology is consistent; examples are
      concrete
- [ ] Workflows have clear steps; quality-critical tasks have feedback loops
- [ ] Scripts handle errors, justify constants, use forward slashes, and declare
      dependencies
- [ ] At least three evaluations exist; tested with every target model and on
      real scenarios
