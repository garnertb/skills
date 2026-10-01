# Dependabot config review: monorepo

## Current state

- Detected ecosystems: `npm` (root, `/apps/*`, `/packages/*`), `github-actions`
  (`.github/workflows/*.yml`).
- Configured in `dependabot.yml`: `npm` at `/` only.
- Gaps: `github-actions` is missing entirely; `/apps/*` and `/packages/*` npm
  packages are not covered, so their updates never open PRs.

## Proposed changes

1. Add directory coverage for the monorepo using globs:

```yaml
- package-ecosystem: "npm"
  directories:
    - "/"
    - "/apps/*"
    - "/packages/*"
  schedule:
    interval: "weekly"
  groups:
    dev-dependencies:
      dependency-type: "development"
      update-types: ["minor", "patch"]
    production-dependencies:
      dependency-type: "production"
      update-types: ["minor", "patch"]
```

2. Add the missing `github-actions` entry:

```yaml
- package-ecosystem: "github-actions"
  directory: "/"
  schedule:
    interval: "weekly"
```

3. Cut PR noise from the same dependency updating across many app/package
   directories by grouping by dependency name:

```yaml
groups:
  monorepo-deps:
    group-by: dependency-name
```

## Tradeoffs

- Grouping by dependency type/name means individual CVEs are less visible in PR
  titles — acceptable here since noise reduction was the stated goal.
- `group-by: dependency-name` only applies to version updates within the same
  ecosystem; incompatible version constraints across directories still split
  into separate PRs.

## Confirm before applying

This is a proposed diff, not yet applied. Confirm the ecosystems, directories,
and grouping strategy above before I update `.github/dependabot.yml`.
