# Dependabot config review: org/payments-api (remote)

## Scan

- Source: remote via `gh api`, repo not checked out locally.
- Ref: default branch `main`, pinned to commit SHA `a1b9f3c`.
- Command: `gh api "repos/org/payments-api/git/trees/a1b9f3c?recursive=1"` (full
  recursive tree, `truncated: false`).
- Completeness: **complete** — all supported ecosystem signatures checked
  against `a1b9f3c`.

I inventory manifests before reading `dependabot.yml`, so coverage gaps are
found independently of what the existing config claims. Note that the repository
language list cannot be used for this: linguist reports languages, so it never
surfaces Dev Containers, GitHub Actions, pre-commit, or submodules.

## Detected ecosystems

| Ecosystem        | Evidence                          | Project root |
| ---------------- | --------------------------------- | ------------ |
| `npm`            | `package.json`                    | `/`          |
| `github-actions` | `.github/workflows/ci.yml`        | `/`          |
| `devcontainers`  | `.devcontainer/devcontainer.json` | `/`          |
| `gitsubmodule`   | `.gitmodules`                     | `/`          |
| `pre-commit`     | `.pre-commit-config.yaml`         | `/`          |

## Existing coverage

`.github/dependabot.yml` configures `npm` at `/` only.

## Gaps

`github-actions`, `devcontainers`, `gitsubmodule`, and `pre-commit` are present
in the repository but absent from the config, so none of them receive version
updates today.

```yaml
- package-ecosystem: "github-actions"
  directory: "/"
  schedule:
    interval: "weekly"

- package-ecosystem: "devcontainers"
  directory: "/"
  schedule:
    interval: "weekly"

- package-ecosystem: "gitsubmodule"
  directory: "/"
  schedule:
    interval: "monthly"
```

## If the scan had been incomplete

For very large repositories the trees API sets `truncated: true`. In that case I
walk the non-recursive subtrees to finish the inventory. If acquisition still
fails — empty repo, 404, missing permission, or rate limit — I report the scan
as incomplete and **do not** list any ecosystem as absent, because an unfinished
scan cannot distinguish "not present" from "not seen".

## Confirm before applying

This is a proposal, not yet applied. Confirm the ecosystems and schedules above
before I update `.github/dependabot.yml`.
