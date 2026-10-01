# Skills

A collection of specialized skills for AI agents to perform specific tasks
effectively.

## Skills

| Category  | Skills                                                                                                                                                                                                                                                               |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `develop` | [pr-feedback-response](skills/develop/pr-feedback-response), [principal-engineer-review](skills/develop/principal-engineer-review), [shell-script-generator](skills/develop/shell-script-generator), [vscode-tasks-organizer](skills/develop/vscode-tasks-organizer) |
| `github`  | [dependabot](skills/github/dependabot)                                                                                                                                                                                                                               |
| `logs`    | [wide-event-logging](skills/logs/wide-event-logging)                                                                                                                                                                                                                 |
| `web`     | [web-interface-guidelines](skills/web/web-interface-guidelines)                                                                                                                                                                                                      |

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
