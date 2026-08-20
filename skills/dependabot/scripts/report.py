#!/usr/bin/env python3
"""Gather a Dependabot report for one or more GitHub repositories.

Collects repo metadata, Dependabot security alerts, Dependabot pull requests,
the ``dependabot.yml`` configuration, and a manifest inventory of every
ecosystem signature present in the file tree, then prints a JSON report to
stdout.

Every section carries an ``ok`` flag and an ``error`` string. The contract is:

    ok == false means nothing may be reported as absent from that section.

A 403 on the alerts endpoint is not "zero alerts", a truncated git tree is not
"no manifests", and a failed contents request is not "no dependabot.yml".

Requires the ``gh`` CLI, authenticated.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from typing import Any

# Basename signatures, in match order. Mirrors the ecosystem table in
# reference/dependabot-config.md; keep the two in sync.
#
# A value containing "|" is an ambiguous signature that a filename alone cannot
# resolve, and is surfaced for confirmation rather than guessed.
ECOSYSTEM_SIGNATURES: tuple[tuple[str, str], ...] = (
    (r"^(package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock)$", "npm"),
    (r"^(requirements([-_].+)?\.txt|Pipfile|setup\.py)$", "pip"),
    (r"^uv\.lock$", "uv"),
    (r"^pyproject\.toml$", "pip|uv"),
    (r"^Dockerfile(\..+)?$", "docker"),
    (r"^docker-compose.*\.ya?ml$", "docker-compose"),
    (r"^go\.mod$", "gomod"),
    (r"^Gemfile$", "bundler"),
    (r"^Cargo\.toml$", "cargo"),
    (r"^composer\.json$", "composer"),
    (r"(\.csproj|^packages\.config)$", "nuget"),
    (r"^global\.json$", "dotnet-sdk"),
    (r"^pom\.xml$", "maven"),
    (r"^build\.gradle(\.kts)?$", "gradle"),
    (r"\.tf$", "terraform|opentofu"),
    (r"^Chart\.yaml$", "helm"),
    (r"^mix\.exs$", "mix"),
    (r"^Package\.swift$", "swift"),
    (r"^pubspec\.yaml$", "pub"),
    (r"^bun\.lockb?$", "bun"),
    (r"^(\.devcontainer\.json|devcontainer\.json)$", "devcontainers"),
    (r"^\.gitmodules$", "gitsubmodule"),
    (r"^\.pre-commit-config\.ya?ml$", "pre-commit"),
)

_COMPILED_SIGNATURES = tuple(
    (re.compile(pattern), ecosystem) for pattern, ecosystem in ECOSYSTEM_SIGNATURES
)

_WORKFLOW_PATH = re.compile(r"^\.github/workflows/[^/]+\.ya?ml$")
_ACTION_FILE = re.compile(r"^action\.ya?ml$")

# Paths that look like dependency manifests but usually belong to vendored code,
# test fixtures, or generated trees. Matched on whole path segments so that
# "src/vendor-utils" is not mistaken for a vendor directory.
_CANDIDATE_ONLY = re.compile(
    r"(^|/)(node_modules|vendor|third_party|testdata|fixtures)(/|$)"
)

# Dependabot accepts either extension, in the .github directory of the default
# branch. Checking only one reports a configured repo as unconfigured.
CONFIG_PATHS = (".github/dependabot.yml", ".github/dependabot.yaml")

TRUNCATED_ERROR = (
    "git tree was truncated; scan is incomplete -- re-run against a local clone "
    "(git clone --filter=blob:none) before reporting any ecosystem as absent"
)
UNKNOWN_SHAPE_ERROR = (
    "unexpected git tree response: no truncated flag, so completeness is unknown"
)


def section(ok: bool, error: str | None, **fields: Any) -> dict[str, Any]:
    """Build a report section with the uniform status contract."""
    return {"ok": ok, "error": error, **fields}


# --- pure classification helpers ---------------------------------------------


def classify(path: str, entry_type: str = "blob") -> str | None:
    """Return the Dependabot ecosystem a tree entry signals, or None."""
    if entry_type == "commit":
        return "gitsubmodule"
    basename = path.rsplit("/", 1)[-1]
    if _WORKFLOW_PATH.match(path) or _ACTION_FILE.match(basename):
        return "github-actions"
    for pattern, ecosystem in _COMPILED_SIGNATURES:
        if pattern.search(basename):
            return ecosystem
    return None


def _to_directory(parts: Iterable[str]) -> str:
    parts = list(parts)
    return "/" + "/".join(parts) if parts else "/"


def directory_for(path: str, ecosystem: str, entry_type: str = "blob") -> str:
    """Return the ``directory`` value a manifest maps to in dependabot.yml.

    Three ecosystems do not use the folder containing the file:

    * ``devcontainers`` resolves ``.devcontainer/devcontainer.json`` relative to
      ``directory``, so ``directory`` is the project root above
      ``.devcontainer`` -- never ``.devcontainer`` itself.
    * ``github-actions`` registers workflow files at the repo root, but a
      composite action at the folder holding its ``action.yml``. That is the
      inverse of the devcontainers rule.
    * ``gitsubmodule`` is declared in the superproject root ``.gitmodules``, so a
      submodule pointer at ``vendor/lib`` still maps to ``/``.
    """
    parts = path.split("/")
    if entry_type == "commit":
        return "/"
    if ecosystem == "devcontainers":
        if ".devcontainer" in parts:
            return _to_directory(parts[: parts.index(".devcontainer")])
        return _to_directory(parts[:-1])
    if ecosystem == "github-actions":
        return "/" if _WORKFLOW_PATH.match(path) else _to_directory(parts[:-1])
    return _to_directory(parts[:-1])


def is_candidate_only(directory: str) -> bool:
    """Whether a configured directory looks vendored, generated, or a fixture.

    Judged on the directory that would be configured, not on the manifest path,
    so a submodule under ``vendor/`` whose directory is ``/`` is not flagged.
    """
    return bool(_CANDIDATE_ONLY.search(directory))


def build_inventory(tree: Any, ref: str | None, sha: str | None) -> dict[str, Any]:
    """Group a git tree response into one entry per (ecosystem, directory) pair.

    Each pair is exactly one ``dependabot.yml`` update block. The contributing
    paths are kept as evidence so any detection can be audited back to a file.

    Fails closed: only an explicit ``truncated: false`` proves the tree was
    whole, so a missing or non-boolean flag is treated as unknown.
    """
    if not isinstance(tree, dict) or not isinstance(tree.get("tree"), list):
        return section(
            False,
            "failed to parse git tree response",
            ref=ref,
            sha=sha,
            entries=[],
        )

    found: dict[tuple[str, str], set[str]] = {}
    for entry in tree["tree"]:
        if not isinstance(entry, dict):
            continue
        entry_type = entry.get("type")
        path = entry.get("path")
        if entry_type not in ("blob", "commit") or not isinstance(path, str):
            continue
        ecosystem = classify(path, entry_type)
        if ecosystem is None:
            continue
        key = (ecosystem, directory_for(path, ecosystem, entry_type))
        found.setdefault(key, set()).add(path)

    entries = [
        {
            "ecosystem": ecosystem,
            "directory": directory,
            "paths": sorted(paths),
            "ambiguous": "|" in ecosystem,
            "candidate_only": is_candidate_only(directory),
        }
        for (ecosystem, directory), paths in sorted(found.items())
    ]

    truncated = tree.get("truncated")
    if truncated is True:
        error = TRUNCATED_ERROR
    elif truncated is False:
        error = None
    else:
        error = UNKNOWN_SHAPE_ERROR

    return section(error is None, error, ref=ref, sha=sha, entries=entries)


def _count_by(names: Iterable[str | None]) -> list[dict[str, Any]]:
    known = [name for name in names if name]
    counts = [
        {"package": name, "count": known.count(name)} for name in sorted(set(known))
    ]
    return sorted(counts, key=lambda item: -item["count"])


def summarize_alerts(alerts: list[dict], include_closed: bool) -> dict[str, Any]:
    """Reduce raw alert payloads to open alerts plus an optional closed rollup."""
    open_alerts = [
        {
            "number": alert.get("number"),
            "state": alert.get("state"),
            "severity": (alert.get("security_advisory") or {}).get("severity"),
            "summary": (alert.get("security_advisory") or {}).get("summary"),
            "package": ((alert.get("dependency") or {}).get("package") or {}).get("name"),
            "ecosystem": ((alert.get("dependency") or {}).get("package") or {}).get(
                "ecosystem"
            ),
            "manifest_path": (alert.get("dependency") or {}).get("manifest_path"),
            "html_url": alert.get("html_url"),
            "created_at": alert.get("created_at"),
            "fixed_at": alert.get("fixed_at"),
            "auto_dismissed_at": alert.get("auto_dismissed_at"),
        }
        for alert in alerts
        if alert.get("state") == "open"
    ]

    closed_summary = None
    if include_closed:
        closed = [alert for alert in alerts if alert.get("state") != "open"]
        closed_summary = {
            "total": len(closed),
            "fixed": len([a for a in closed if a.get("state") == "fixed"]),
            "dismissed": len(
                [
                    a
                    for a in closed
                    if a.get("state") in ("dismissed", "auto_dismissed")
                ]
            ),
            "by_package": _count_by(
                [
                    ((a.get("dependency") or {}).get("package") or {}).get("name")
                    for a in closed
                ]
            ),
        }

    return {"open": open_alerts, "closed_summary": closed_summary}


_DEPENDENCY_TITLE = re.compile(
    r"^(?:build|chore)\(deps(?:-dev)?\): bump (?P<pkg>\S+)"
)


def _dependency_name(title: str) -> str:
    match = _DEPENDENCY_TITLE.match(title or "")
    return match.group("pkg") if match else title


def _ci_status(rollup: Any) -> str:
    if not isinstance(rollup, list):
        return ""
    results = {
        check.get("conclusion") or check.get("state")
        for check in rollup
        if isinstance(check, dict)
    }
    return ",".join(sorted(result for result in results if result))


def summarize_prs(prs: list[dict], include_closed: bool) -> dict[str, Any]:
    """Reduce raw pull request payloads to open PRs plus an optional rollup."""
    open_prs = [
        {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "url": pr.get("url"),
            "state": pr.get("state"),
            "branch": pr.get("headRefName"),
            "created_at": pr.get("createdAt"),
            "closed_at": pr.get("closedAt"),
            "ci_status": _ci_status(pr.get("statusCheckRollup")),
        }
        for pr in prs
        if pr.get("state") == "OPEN"
    ]

    closed_summary = None
    if include_closed:
        closed = [pr for pr in prs if pr.get("state") != "OPEN"]
        closed_summary = {
            "total": len(closed),
            "merged": len([pr for pr in closed if pr.get("state") == "MERGED"]),
            "closed_unmerged": len(
                [pr for pr in closed if pr.get("state") == "CLOSED"]
            ),
            "by_package": _count_by(
                [_dependency_name(pr.get("title", "")) for pr in closed]
            ),
        }

    return {"open": open_prs, "closed_summary": closed_summary}


def normalize_repo(raw: dict) -> dict[str, Any]:
    """Flatten `gh repo view` output into the report's metadata fields."""
    return {
        "name": raw.get("name"),
        "name_with_owner": raw.get("nameWithOwner"),
        "url": raw.get("url"),
        "is_archived": raw.get("isArchived"),
        "is_fork": raw.get("isFork"),
        "is_private": raw.get("isPrivate"),
        "visibility": raw.get("visibility"),
        "default_branch": (raw.get("defaultBranchRef") or {}).get("name"),
        "pushed_at": raw.get("pushedAt"),
        "updated_at": raw.get("updatedAt"),
        "primary_language": (raw.get("primaryLanguage") or {}).get("name"),
        "languages": [
            (lang.get("node") or {}).get("name") for lang in raw.get("languages") or []
        ],
        "is_security_policy_enabled": raw.get("isSecurityPolicyEnabled"),
        "security_policy_url": raw.get("securityPolicyUrl"),
        "owner": (raw.get("owner") or {}).get("login"),
        "is_in_organization": raw.get("isInOrganization"),
    }


# --- gh transport -------------------------------------------------------------


class GitHubError(Exception):
    """A gh invocation failed or returned something unparseable."""


def run_gh(args: list[str]) -> Any:
    """Run gh and parse its stdout as JSON.

    gh writes API error bodies to stdout, so success is decided by exit status
    and never by the output being non-empty.
    """
    try:
        result = subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise GitHubError(f"could not run gh: {exc}") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        raise GitHubError(detail[0] if detail else f"gh exited {result.returncode}")

    text = result.stdout.strip()
    if not text:
        raise GitHubError("gh returned no output")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # --paginate concatenates one JSON document per page. Decode them in
    # sequence rather than splitting on brackets, which nested arrays break.
    decoder = json.JSONDecoder()
    documents: list[Any] = []
    index = 0
    while index < len(text):
        try:
            document, index = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise GitHubError("could not parse gh output as JSON") from exc
        documents.append(document)
        while index < len(text) and text[index].isspace():
            index += 1

    if documents and all(isinstance(page, list) for page in documents):
        return [item for page in documents for item in page]
    raise GitHubError("could not parse gh output as JSON")


def fetch_alerts(repo: str, include_closed: bool) -> dict[str, Any]:
    query = "" if include_closed else "?state=open"
    try:
        alerts = run_gh(["api", f"repos/{repo}/dependabot/alerts{query}", "--paginate"])
    except GitHubError as exc:
        return section(
            False,
            f"could not fetch alerts ({exc}); alert absence cannot be concluded",
            open=[],
            closed_summary=None,
        )
    if not isinstance(alerts, list):
        return section(
            False, "unexpected alerts response", open=[], closed_summary=None
        )
    return section(True, None, **summarize_alerts(alerts, include_closed))


def fetch_prs(repo: str, include_closed: bool) -> dict[str, Any]:
    try:
        prs = run_gh(
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--app",
                "dependabot",
                "--state",
                "all" if include_closed else "open",
                "--limit",
                "500",
                "--json",
                "number,title,url,state,headRefName,createdAt,closedAt,mergedAt,"
                "statusCheckRollup",
            ]
        )
    except GitHubError as exc:
        return section(
            False,
            f"could not list pull requests ({exc})",
            open=[],
            closed_summary=None,
        )
    if not isinstance(prs, list):
        return section(
            False, "unexpected pull request response", open=[], closed_summary=None
        )
    return section(True, None, **summarize_prs(prs, include_closed))


def fetch_config(repo: str) -> dict[str, Any]:
    """Look for dependabot.yml and dependabot.yaml, distinguishing 404 from error."""
    errors = []
    for path in CONFIG_PATHS:
        try:
            raw = run_gh(["api", f"repos/{repo}/contents/{path}"])
        except GitHubError as exc:
            message = str(exc)
            # A 404 is a real absence. Anything else means we could not see.
            if "404" not in message and "Not Found" not in message:
                errors.append(f"{path}: {message}")
            continue

        content = raw.get("content") if isinstance(raw, dict) else None
        if not isinstance(content, str):
            errors.append(f"{path}: contents response had no content field")
            continue
        try:
            decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        except (ValueError, TypeError) as exc:
            return section(False, f"could not decode {path}: {exc}", present=None)
        return section(True, None, present=True, path=path, raw=decoded)

    if errors:
        return section(
            False,
            "; ".join(errors) + "; config absence cannot be concluded",
            present=None,
        )
    return section(True, None, present=False, path=None, raw=None)


def fetch_metadata(repo: str) -> dict[str, Any]:
    try:
        raw = run_gh(
            [
                "repo",
                "view",
                repo,
                "--json",
                "name,nameWithOwner,url,isArchived,isFork,isPrivate,visibility,"
                "defaultBranchRef,pushedAt,updatedAt,primaryLanguage,languages,"
                "isSecurityPolicyEnabled,securityPolicyUrl,owner,isInOrganization",
            ]
        )
    except GitHubError as exc:
        return section(False, f"could not fetch repo metadata ({exc})")
    if not isinstance(raw, dict):
        return section(False, "unexpected repo metadata response")
    return section(True, None, **normalize_repo(raw))


def fetch_manifests(repo: str) -> dict[str, Any]:
    """Walk the default branch file tree and inventory ecosystem signatures.

    The repo language list cannot be used here: linguist reports languages, so it
    never surfaces Dev Containers, Actions, pre-commit, or submodules.
    """
    try:
        repo_info = run_gh(["api", f"repos/{repo}"])
        branch = repo_info.get("default_branch") if isinstance(repo_info, dict) else None
    except GitHubError:
        branch = None
    if not isinstance(branch, str) or not branch:
        return section(
            False,
            "could not resolve default branch (empty repo, not found, or no access)",
            ref=None,
            sha=None,
            entries=[],
        )

    # Resolve to a commit SHA via a query param so branch names containing "/"
    # cannot break the request path, and so every entry comes from one snapshot.
    try:
        commits = run_gh(["api", f"repos/{repo}/commits?sha={branch}&per_page=1"])
        sha = commits[0].get("sha") if isinstance(commits, list) and commits else None
    except GitHubError:
        sha = None
    if not isinstance(sha, str) or not sha:
        return section(
            False,
            "could not resolve a commit for the default branch",
            ref=branch,
            sha=None,
            entries=[],
        )

    try:
        tree = run_gh(["api", f"repos/{repo}/git/trees/{sha}?recursive=1"])
    except GitHubError as exc:
        return section(
            False,
            f"git trees request failed ({exc})",
            ref=branch,
            sha=sha,
            entries=[],
        )

    return build_inventory(tree, branch, sha)


def report_for_repo(repo: str, include_closed: bool) -> dict[str, Any]:
    sections = {
        "metadata": fetch_metadata(repo),
        "alerts": fetch_alerts(repo, include_closed),
        "pull_requests": fetch_prs(repo, include_closed),
        "config": fetch_config(repo),
        "manifest_inventory": fetch_manifests(repo),
    }
    return {
        "repo": repo,
        "ok": all(part["ok"] for part in sections.values()),
        **sections,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="report.py",
        description=(
            "Gather Dependabot alerts, pull requests, configuration, and a "
            "manifest inventory for one or more repos as JSON."
        ),
        epilog=(
            "Every section reports ok and error. When ok is false, nothing may "
            "be reported as absent from that section."
        ),
    )
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="also fetch and summarize closed alerts and pull requests",
    )
    parser.add_argument("repos", nargs="+", metavar="owner/repo")
    args = parser.parse_args(argv)

    if shutil.which("gh") is None:
        print("error: gh CLI is required", file=sys.stderr)
        return 1

    # One unreachable repo must not discard the reports already gathered.
    reports = []
    for repo in args.repos:
        try:
            reports.append(report_for_repo(repo, args.include_closed))
        except Exception as exc:  # noqa: BLE001 - one repo must not abort the run
            reports.append(
                {"repo": repo, "ok": False, "error": f"report failed: {exc}"}
            )

    json.dump(reports, sys.stdout, indent=2)
    sys.stdout.write("\n")
    # A degraded section is reported in-band via ok/error, not via exit status,
    # so callers never discard an otherwise usable report.
    return 0


if __name__ == "__main__":
    sys.exit(main())
