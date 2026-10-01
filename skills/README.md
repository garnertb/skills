## Skills

Agent Skills are a lightweight, open format for extending AI agent capabilities
with specialized knowledge and workflows.

At its core, a skill is a folder containing a SKILL.md file. This file includes
metadata (name and description, at minimum) and instructions that tell an agent
how to perform a specific task. Skills can also bundle scripts, templates, and
reference materials.

```
my-skill/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

In this repository, skills are grouped by purpose under category folders:
`skills/<category>/<skill-name>/` (`dev-tooling`, `engineering`, `github`,
`logs`).

## References

- [Skill Specification](https://agentskills.io/specification)
