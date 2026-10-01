# Ecosystems to configure

## Detected

| Ecosystem        | Evidence                                          | Project root       |
| ---------------- | ------------------------------------------------- | ------------------ |
| `devcontainers`  | `.devcontainer/devcontainer.json`                 | `/`                |
| `devcontainers`  | `services/worker/.devcontainer/devcontainer.json` | `/services/worker` |
| `github-actions` | `.github/workflows/ci.yml`                        | `/`                |
| `gitsubmodule`   | `.gitmodules`                                     | `/`                |
| `npm`            | `package.json`                                    | `/`                |
| `uv`             | `services/worker/pyproject.toml` + `uv.lock`      | `/services/worker` |

Two notes on the mapping:

- **`uv`, not `pip`.** `pyproject.toml` alone is ambiguous between the two;
  `services/worker/uv.lock` resolves it to `uv`.
- **`devcontainers` `directory` is the project root, not the `.devcontainer`
  folder.** Dependabot searches `.devcontainer.json`,
  `.devcontainer/devcontainer.json`, and
  `.devcontainer/<name>/devcontainer.json` _relative to_ the configured
  directory. So `.devcontainer/devcontainer.json` needs `directory: "/"`.
  Setting `directory: "/.devcontainer"` makes Dependabot look for
  `/.devcontainer/.devcontainer.json`, which does not exist, and the entry
  silently does nothing.

## Needs confirmation

`test/fixtures/sample-project/.devcontainer/devcontainer.json` is under a test
fixture path. It is a candidate rather than a detection — configuring it would
open PRs against fixture data. Confirm whether you want it covered; I have left
it out below.

## Proposed config

```yaml
version: 2
updates:
  - package-ecosystem: "devcontainers"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "devcontainers"
    directory: "/services/worker"
    schedule:
      interval: "weekly"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "gitsubmodule"
    directory: "/"
    schedule:
      interval: "monthly"

  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "uv"
    directory: "/services/worker"
    schedule:
      interval: "weekly"
```

## Tradeoffs

- `gitsubmodule` is set to `monthly` because submodule bumps are usually
  low-urgency and noisy; raise it to `weekly` if these track active internal
  repos.
- Six entries will produce a noticeable PR volume. If that is too much, group
  the two `devcontainers` entries and the two workspace ecosystems once you see
  the real rate.

## Confirm before applying

Confirm the ecosystem list, the fixture decision, and the schedules above before
I write `.github/dependabot.yml`.
