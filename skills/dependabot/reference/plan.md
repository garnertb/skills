# Dependabot plan

Analyze Dependabot findings and produce a tiered, risk-based remediation
strategy. This command turns raw findings into a prioritized execution plan,
especially when multiple updates compete for limited engineering time.

## Inputs

Use report output as the starting point for your analysis.

1. Run [scripts/report.py](../scripts/report.py) for target repos:

```bash
scripts/report.py owner/repo [owner/repo ...]
scripts/report.py --include-closed owner/repo [owner/repo ...]
```

2. Parse these sections for each repo:

- `metadata`
- `alerts.open` and (optionally) `alerts.closed_summary`
- `pull_requests.open` and (optionally) `pull_requests.closed_summary`
- `config`

Each section carries `ok` and `error`. If a section's `ok` is `false`, treat it
as unknown rather than empty — do not plan against an absence it did not
establish.

## Risk model

Assign each update candidate to one of four tiers. Consider all dimensions, not
just semver level.

### Tier 0 (Critical)

- Active exploit or known exploitable CVE
- Production-facing runtime dependency
- Major version bump or breaking API behavior likely
- High integration surface in application code

Action: immediate remediation and accelerated validation.

### Tier 1 (High)

- High/Critical alert without confirmed active exploit
- Runtime dependency with broad usage
- Minor or major bump with moderate-to-high integration risk

Action: prioritize in current sprint with targeted testing and staged rollout.

### Tier 2 (Moderate)

- Medium severity alerts or non-security freshness updates
- Limited runtime usage or moderate tooling impact
- Patch/minor bumps with manageable compatibility risk

Action: batch into scheduled maintenance windows.

### Tier 3 (Low)

- Dev/test/build-only dependencies with low blast radius
- Patch bumps with no notable behavior change
- Minimal integration surface

Action: auto-merge policy candidate after baseline checks.

## High-risk analysis requirements

For Tier 0 and Tier 1 items, ALWAYS perform both analyses below before
finalizing the plan.

### 1. Changelog and release-note analysis

Collect and summarize:

- Breaking changes, migration guides, removed APIs
- Security-specific notes and exploit context
- Runtime behavior changes (defaults, parsing, auth, crypto, IO, networking)
- Transitive dependency shifts that alter risk posture

Record:

- `change_risk`: `low | medium | high`
- `breaking_change_present`: `true | false`
- `required_migration_steps`: explicit checklist

### 2. Integration-point analysis in codebase

Map how the dependency is used:

- Direct imports/usages across services and packages
- Wrappers, adapters, middleware, or shared utility usage
- Security-sensitive paths (authn/authz, input validation, secrets, crypto)
- Data-plane and user-facing execution paths

Validate:

- Existing tests that cover touched paths
- Missing tests required before merge
- Rollback and feature-flag options

Record:

- `integration_surface`: `narrow | moderate | broad`
- `critical_paths_touched`: list
- `test_coverage_confidence`: `low | medium | high`

## Prioritization workflow

For each open alert/PR candidate:

1. Classify ecosystem and dependency scope (runtime vs tooling).
2. Score risk dimensions:

- Security urgency (CVE severity, exploitability, exposure)
- Compatibility risk (semver jump, API churn)
- Integration surface (usage breadth, critical paths)
- Verification readiness (test coverage, rollout control)

3. Assign tier (0-3).
4. Choose execution strategy:

- Fast-track hotfix
- Standard sprint work
- Batched maintenance
- Defer with explicit rationale and review date

5. Define validation depth by tier.
6. Build a sequenced backlog with owner and due window.

## Output format

Return a concise, structured plan per repo with these sections:

1. Executive summary

- Total open alerts/PRs
- Tier distribution
- Immediate actions (next 24-72h)

2. Tiered remediation queue

- `dependency`
- `from_version` -> `to_version`
- `tier`
- `risk_rationale`
- `execution_strategy`
- `required_validation`
- `owner`
- `target_window`

3. High-risk deep dives (Tier 0/1 only)

- Changelog findings
- Integration-point map
- Required migrations
- Test and rollout plan
- Rollback plan

4. Policy recommendations

- Candidates for auto-merge guardrails
- Repos/ecosystems missing in `dependabot.yml`
- CI/test improvements needed to reduce future risk

## Guardrails

- Do not recommend blind auto-merge for Tier 0/1 updates.
- Do not classify risk from semver alone.
- Flag archived repos explicitly: findings are stale snapshots.
- If evidence is missing (no changelog, unclear integration points), keep or
  raise risk tier and call out the uncertainty.
