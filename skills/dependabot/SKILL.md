---
name: dependabot
description: >
  Use when user wants to work with Dependabot PRs, alerts, or the Dependabot
  configuration file. Triggers on: "dependabot", "dependabot PRs", "dependabot
  alerts", "dependabot.yml", "dependabot configuration", "configure dependabot".
  Works with any ecosystem (npm, pip, cargo, go, maven, etc.) and GitHub
  Actions. Do NOT trigger for: setting up auto-merge, reviewing a single PR,
  running npm audit, or building dependency dashboards.
argument-hint: "[report|plan · config] [target]"
user-invocable: true
metadata:
  version: 1.1.2
---

## Overview

Use this skill when working with Dependabot PRs, alerts, or the Dependabot
configuration file. Dependabot is GitHub's built-in dependency management tool
with three core capabilities:

1. **Dependabot Alerts** — Notify when dependencies have known vulnerabilities
   (CVEs)
2. **Dependabot Security Updates** — Auto-create PRs to fix vulnerable
   dependencies
3. **Dependabot Version Updates** — Auto-create PRs to keep dependencies current

All configuration lives in a **single file**: `.github/dependabot.yml` on the
default branch. GitHub does **not** support multiple `dependabot.yml` files per
repository.

To act on an existing PR via `@dependabot` comments (rebase, recreate, ignore a
version, etc.), see the
[PR Comment Commands](./reference/dependabot-config.md#pr-comment-commands)
section of the config reference rather than editing `dependabot.yml`.

For pre-commit dependency vulnerability scanning inside an AI coding agent, the
GitHub MCP Server's `dependabot` toolset and the Advanced Security plugin's
`/dependency-scanning` skill can check newly added dependencies against the
GitHub Advisory Database before the user commits — point the user to those if
they ask about scanning changes rather than managing existing alerts/PRs.

## Commands

| Command  | Category  | Description                                                                            | Reference                                    |
| -------- | --------- | -------------------------------------------------------------------------------------- | -------------------------------------------- |
| `report` | Analyze   | Produce a status report of Dependabot alerts, PRs, and configuration                   | [reference/report.md](./reference/report.md) |
| `plan`   | Analyze   | Analyze findings to produce a tiered, risk-based plan for resolving Dependabot updates | [reference/plan.md](./reference/plan.md)     |
| `config` | Configure | Create or improve `.github/dependabot.yml`: ecosystems, grouping, scheduling, security | [reference/config.md](./reference/config.md) |

Routing:

- **No argument:** read [routing.md](./reference/routing.md) and present its
  context-aware menu; never auto-run a command.
- **Explicit or clearly implied command:** load its reference (native variant on
  native platforms) and follow it. Ask once if two commands fit.
- **Otherwise:** treat the request as general question about Dependabot.
