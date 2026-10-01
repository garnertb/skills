# Dependabot config

Help the user create or improve `.github/dependabot.yml`. Use this command when
they want to add an ecosystem, reduce PR noise, tune scheduling, or ask "is my
Dependabot config good?" Treat it as a conversation, not a one-shot rewrite:
propose changes, explain the tradeoffs, and confirm before editing the file.

Reminder: only one `.github/dependabot.yml` file is supported per repo, on the
default branch. Everything below lives inside that file's `updates:` array
(unless noted otherwise).

For every option, table, and YAML example referenced by the steps below, see
[dependabot-config.md](./dependabot-config.md) — that's the single source of
truth; don't duplicate its content here.

## Workflow

1. **Inventory manifests, then detect ecosystems** — build the inventory
   _before_ looking at any existing `dependabot.yml`, so discovery is
   independent of what the config already claims. Map each manifest to its
   `package-ecosystem` value
   ([ecosystem table](./dependabot-config.md#step-1-detect-all-ecosystems),
   [manifest location notes](./dependabot-config.md#manifest-location-notes)).

   Resolve the target first — the repo under review is often **not** checked out
   locally:
   - **Remote repo** (or no local checkout): run
     `scripts/report.py <owner/repo>` and use its `manifest_inventory` key. It
     walks the full file tree at a pinned commit, so it sees dotfiles and nested
     paths, and returns one entry per (ecosystem, `directory`) pair with the
     `directory` already resolved — use it as given rather than re-deriving it
     from `paths`. Do not derive ecosystems from the repo `languages` list —
     linguist reports languages, so it structurally cannot see `devcontainers`,
     `github-actions`, `pre-commit`, or `gitsubmodule`.
   - **Local checkout**: the analysis target is the _working tree_, so list both
     tracked and non-ignored untracked files — `git ls-files` **and**
     `git ls-files --others --exclude-standard`. A manifest that was just added
     and not yet committed is a common reason to run this command;
     `git ls-files` alone would miss it.

   Two rules on completeness:
   - Match on full paths, not top-level entries. Manifests hide in dot
     directories (`.devcontainer/`, `.github/workflows/`) and nested packages.
   - **Never report an ecosystem as absent from an incomplete scan.** If
     `manifest_inventory.ok` is `false`, or the local listing failed, say the
     scan was incomplete and what would complete it — an unverified "not
     detected" reads as authoritative and is worse than silence.

   Flag rather than guess: manifests under `node_modules/`, `vendor/`,
   `testdata/`, or fixture paths are candidates needing confirmation, and
   ambiguous signatures (`pyproject.toml` → `pip` vs `uv`; `*.tf` → `terraform`
   vs `opentofu`) must be confirmed, not assumed.

2. **Map directory coverage** — every `manifest_inventory` entry is already one
   update block, so start from that list rather than inventing locations. Use
   `directories` (plural) with globs to collapse a monorepo that produced many
   entries sharing an ecosystem, since `directory` (singular) doesn't support
   wildcards — but only when the glob cannot pull in paths the scan flagged as
   `candidate_only`
   ([directory locations](./dependabot-config.md#step-2-map-directory-locations)).
3. **Confirm a baseline entry** exists for every detected ecosystem before
   layering on optimizations
   ([baseline entry](./dependabot-config.md#step-3-configure-each-ecosystem-entry)).
4. **Reduce PR noise with grouping**, if the user is drowning in individual PRs
   — by dependency type, name pattern, security updates, or
   `group-by: dependency-name` for monorepos
   ([grouping](./dependabot-config.md#dependency-grouping),
   [monorepo strategies](./dependabot-config.md#monorepo-strategies),
   [multi-ecosystem groups](./dependabot-config.md#multi-ecosystem-groups)).
5. **Tune scheduling** — interval, cron, and cooldowns; suggest longer intervals
   or cooldowns for low-priority ecosystems instead of disabling updates
   outright
   ([schedule optimization](./dependabot-config.md#schedule-optimization)).
6. **Set PR metadata** — labels, commit-message prefixes, assignees, milestones,
   branch separator, target branch
   ([PR customization](./dependabot-config.md#pr-customization)).
7. **Check security-specific settings** — alerts/security updates are enabled in
   repo Settings, not YAML; group security PRs; `open-pull-requests-limit: 0` to
   go security-only; consider recommending a `cooldown` for version updates, but
   call out that it has **no effect on security updates**, which always go out
   immediately
   ([security updates](./dependabot-config.md#security-updates-configuration)).
8. **Apply ignore/allow rules** — exclude dependencies, versions, or paths;
   remember a dependency matching both `allow` and `ignore` is ignored
   ([ignore and allow rules](./dependabot-config.md#ignore-and-allow-rules)).
9. **Ask before applying advanced options** — `versioning-strategy`,
   `rebase-strategy`, `open-pull-requests-limit`, private registries
   ([advanced options](./dependabot-config.md#advanced-options)).

## Output format

Keep the per-step checklist internal; report only what the user needs to act on.

1. State the **scan source and ref** and whether it was complete — e.g. "full
   tree scan of `owner/repo` at `main` (`a1b2c3d`)" or "working tree, tracked +
   untracked". When the scan was complete, one line covers it: all supported
   ecosystem signatures were checked. When it was not, say so explicitly and
   name what would complete it.
2. List **detected ecosystems with their locations**, then **what the existing
   config already covers**, then the **gaps** — don't merge coverage and
   detection into one verdict.
3. List **ambiguities and candidates** needing confirmation (vendored or fixture
   paths, `pyproject.toml`, `*.tf`) as questions, not decisions.
4. Propose specific changes as a diff or full file, grouped by the workflow step
   they address.
5. Call out any tradeoffs (e.g., grouping hides individual CVEs in the PR title;
   longer intervals delay both features and fixes).
6. Only write to `.github/dependabot.yml` after the user confirms the direction
   — don't silently overwrite an existing config.

## FAQ

**Can I have multiple `dependabot.yml` files?** No — one file, one `updates:`
array with multiple entries.

**Does Dependabot support pnpm/yarn?** Yes, under the `npm` ecosystem value;
lockfile detection is automatic.

**How do I cut PR noise in a monorepo?** Combine `directories` globs, `groups`,
and `group-by: dependency-name`; consider `monthly`/`quarterly` intervals for
low-priority ecosystems.

**How do I handle a dependency outside the main workspace?** Give it its own
ecosystem entry with a `directory` pointing at that location.
