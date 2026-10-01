# Skills

A collection of specialized skills for AI agents to perform specific tasks
effectively.

## Skills

| Category      | Skills                                                                                                                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dev-tooling` | [shell-script-generator](skills/dev-tooling/shell-script-generator), [vscode-tasks-organizer](skills/dev-tooling/vscode-tasks-organizer)                                                                            |
| `engineering` | [pr-feedback-response](skills/engineering/pr-feedback-response), [principal-engineer-review](skills/engineering/principal-engineer-review), [web-interface-guidelines](skills/engineering/web-interface-guidelines) |
| `github`      | [dependabot](skills/github/dependabot)                                                                                                                                                                              |
| `logs`        | [wide-event-logging](skills/logs/wide-event-logging)                                                                                                                                                                |

## Installation

Install all skills with the following command:

```bash
npx skills add garnertb/skills --all
```

### Install Specific Skill

```bash
npx skills add garnertb/skills --skill <skill-name>
```

## Validation

To validate all skills, run the following command in your terminal:

```bash
./scripts/validate-skills
```

To validate a specific skill, provide the skill name (or
`<category>/<skill-name>`) as an argument:

```bash
./scripts/validate-skills <skill-name>
```
