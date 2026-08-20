# Dependabot report

Produce a report of Dependabot security alerts, PRs, and the dependabot
configuration for the given repo/s.

## Task

Gather and summarize the following information for the given repo/s:

- Dependabot security alerts (open and closed) with their severity, status, and
  any associated PRs.
- Dependabot PRs (open and closed) with their dependency name, version change,
  semver level (patch/minor/major), ecosystem, and CI status.
- Current dependabot configuration (from `dependabot.yml`), including the
  ecosystems, package managers, and update schedules.
- Repo context that affects how the above should be interpreted: whether the
  repo is archived, a fork, or private (Dependabot alerts/updates behave
  differently in each case), and the default branch. Call out archived repos
  explicitly — **Dependabot does not run on archived repos**, so any alerts/PRs
  shown are frozen as of the archive date, not current.
- Ecosystems present in the code but missing from `dependabot.yml`, derived from
  `manifest_inventory` (see below) — **not** from the repo's `languages` list,
  which is narrative context only.

## Gathering data

Run [scripts/report.py](../scripts/report.py) to fetch repo metadata, alerts,
PRs, a manifest inventory, and the `dependabot.yml` config for one or more repos
in a single JSON payload instead of making separate `gh` calls:

```bash
scripts/report.py owner/repo [owner/repo ...]
scripts/report.py --include-closed owner/repo [owner/repo ...]
scripts/report.py --output report.json owner/repo   # large repos
```

Requires Python 3.9+ and the `gh` CLI (authenticated). Use the JSON output as
the source of truth when building the report below.

### Large repositories

The payload scales with the number of manifests: a monorepo can exceed 50K
characters, past the point where a harness may truncate tool output. The script
warns on stderr when the stdout payload is large. When that happens — or
pre-emptively for a repo you expect to be big — pass `--output FILE` and query
the file rather than reading a silently truncated payload:

```bash
scripts/report.py --output report.json owner/repo
jq '.[0].manifest_inventory.entries[] | {ecosystem, directory}' report.json
```

With `--output`, stdout carries a one-line summary per repo and the full JSON
goes to the file.

### Exit codes

| Code | Meaning                                                           |
| ---- | ----------------------------------------------------------------- |
| `0`  | A report was produced. Individual sections may still be degraded. |
| `2`  | Invalid arguments — for example a repo not in `owner/repo` form.  |
| `3`  | `gh` is missing or unauthenticated.                               |
| `4`  | No repository could be reported at all.                           |

Progress diagnostics go to stderr, so stdout stays parseable JSON.

### Reading a degraded payload

Every section (`metadata`, `alerts`, `pull_requests`, `config`,
`manifest_inventory`) carries `ok` and `error`, and the top-level `ok` is the
AND of all of them. One rule governs all five:

> **If a section's `ok` is `false`, nothing may be reported as absent from that
> section.** Report the `error` instead.

This matters because the common failures look exactly like good news. A 403 on
the alerts endpoint — routine without admin rights — would otherwise read as
"zero alerts", and an unreadable file tree would read as "no ecosystems
missing". A degraded section is not a failed run: the script still exits `0` and
the other sections stay usable.

By default only open alerts and open PRs are fetched in full, and
`closed_summary` is `null` for both — pass `--include-closed` when the task
needs closed/fixed/dismissed alerts or closed/merged PRs. Both `alerts` and
`pull_requests` share the same shape to keep noisy history out of the report:

- `open`: full detail for every open alert/PR (severity, package, URL, CI
  status, etc.).
- `closed_summary` (only populated with `--include-closed`): counts only —
  totals split by state (`fixed`/`dismissed` for alerts,
  `merged`/`closed_unmerged` for PRs) plus a `by_package` breakdown of how many
  closed items touched each dependency. Use this for the "open and closed" task
  items below instead of listing every closed row.

The `metadata` field gives context that changes how the alerts/PRs should be
read: `is_archived`/`is_fork`/`is_private`/`visibility`, `default_branch`,
`pushed_at`/`updated_at` (repo activity), `primary_language`/`languages`, and
`is_security_policy_enabled`. If `is_archived` is `true`, lead with that in the
report — Dependabot stops scanning archived repos entirely, so the
alerts/pull_requests data is a stale snapshot, not live status. Also call out
unmaintained repos (`pushed_at` far in the past) where open PRs/alerts may never
be addressed.

The `manifest_inventory` field is the source of truth for ecosystem gaps. It is
a full file-tree scan pinned to one commit, so it sees dotfiles and nested
manifests that `languages` cannot:

- `ok` / `error`: whether the scan is trustworthy. **If `ok` is `false`, do not
  report any ecosystem as absent** — say the scan was incomplete and surface
  `error`.
- `ref` / `sha`: the branch and commit scanned. Cite these in the report.
- `entries[]`: one entry per **(ecosystem, directory) pair**, which is exactly
  one `dependabot.yml` update block:
  - `ecosystem` — the `package-ecosystem` value.
  - `directory` — the `directory` value. Already resolved; do not re-derive it
    from `paths`, since the correct value is not always the folder holding the
    manifest (see
    [manifest location notes](./dependabot-config.md#manifest-location-notes)).
  - `paths[]` — the manifests that justify the pair. Evidence, not input: cite
    them when reporting a detection.
  - `ambiguous` — the signature maps to more than one ecosystem (`pip|uv`,
    `terraform|opentofu`), so confirm rather than assume.
  - `candidate_only` — every supporting path is vendored, generated, or a
    fixture, so it usually should not be configured.

Flag any `entries[].ecosystem` with no matching entry in `config.raw`. The
`config` section reports `present` (whether a config file exists) and `path`
(which of `.github/dependabot.yml` or `.github/dependabot.yaml` was found).

## Output

Produce a report in a structured format (e.g., JSON, Markdown, or table) that
summarizes the above information for each repo. Include any relevant links to
the alerts, PRs, and configuration files.

The rendered report **is** the deliverable. Keep the surrounding chat lean:

- Do **not** follow the report with a prose recap of the same findings (no "Key
  findings", "Recommendations given", or "The report is delivered" sections) —
  it duplicates content the report already contains.
- Do **not** add meta-commentary about having finished or about `report` being
  an analyze-only command.
- After the report, at most **one short line** offering a logical next step
  (e.g. `/dependabot plan` or `/dependabot config`). Omit it if nothing applies.
