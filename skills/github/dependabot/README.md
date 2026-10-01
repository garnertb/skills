# Dependabot

A skill for working with Dependabot alerts, pull requests, and the
`.github/dependabot.yml` configuration file across any ecosystem (npm, pip,
cargo, go, maven, and more) plus GitHub Actions.

## Overview

Dependabot is GitHub's built-in dependency management tool with three core
capabilities:

1. **Alerts** — notify when dependencies have known vulnerabilities (CVEs)
2. **Security Updates** — auto-create PRs to fix vulnerable dependencies
3. **Version Updates** — auto-create PRs to keep dependencies current

All configuration lives in a single file, `.github/dependabot.yml`, on the
default branch.

## Commands

| Command  | Category  | Description                                                          |
| -------- | --------- | -------------------------------------------------------------------- |
| `report` | Analyze   | Status report of Dependabot alerts, PRs, and configuration           |
| `plan`   | Analyze   | Tiered, risk-based plan for resolving Dependabot updates             |
| `config` | Configure | Create or improve `dependabot.yml`: ecosystems, grouping, scheduling |

Invoke with a command and optional target, e.g. `report`, `plan`, or
`config · <repo>`. With no argument, the skill presents a context-aware menu.
