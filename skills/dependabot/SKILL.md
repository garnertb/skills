---
name: dependabot
description: >
  Use when user wants to work with Dependabot PRs, alerts, or the Dependabot
  configuration file. Triggers on: "dependabot", "dependabot PRs", "dependabot
  alerts", "dependabot.yml", "dependabot configuration". Works with any
  ecosystem (npm, pip, cargo, go, maven, etc.) and GitHub Actions. Do NOT
  trigger for: configuring dependabot.yml, setting up auto-merge, reviewing a
  single PR, running npm audit, or building dependency dashboards.
metadata:
  version: 1.0.0
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

## Commands

| Command  | Category | Description                                                                            | Reference                                    |
| -------- | -------- | -------------------------------------------------------------------------------------- | -------------------------------------------- |
| `report` | Analyze  | Produce a status report of Dependabot alerts, PRs, and configuration                   | [reference/report.md](./reference/report.md) |
| `plan`   | Analyze  | Analyze findings to produce a tiered, risk-based plan for resolving Dependabot updates | [reference/plan.md](./reference/plan.md)     |

Routing:

- **No argument:** read [routing.md](./reference/routing.md) and present its
  context-aware menu; never auto-run a command.
- **Explicit or clearly implied command:** load its reference (native variant on
  native platforms) and follow it. Ask once if two commands fit.
- **Otherwise:** treat the request as general question about Dependabot.
