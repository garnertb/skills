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

1. **Detect ecosystems** — scan the repo for manifests and map each to its
   `package-ecosystem` value
   ([ecosystem table](./dependabot-config.md#step-1-detect-all-ecosystems)).
2. **Map directory coverage** — give every ecosystem at least one location; use
   `directories` (plural) with globs for monorepos, since `directory` (singular)
   doesn't support wildcards
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

1. Summarize current state: ecosystems found, ecosystems already configured, and
   gaps.
2. Propose specific changes as a diff or full file, grouped by the step above
   they address.
3. Call out any tradeoffs (e.g., grouping hides individual CVEs in the PR title;
   longer intervals delay both features and fixes).
4. Only write to `.github/dependabot.yml` after the user confirms the direction
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
