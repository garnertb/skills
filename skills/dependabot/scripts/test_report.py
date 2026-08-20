#!/usr/bin/env python3
"""Tests for report.py. Pure functions only -- nothing here touches the network."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import report  # noqa: E402


def tree(*entries: tuple[str, str], truncated: bool | None = False) -> dict:
    """Build a git trees API response from (path, type) pairs."""
    payload: dict = {"tree": [{"path": path, "type": kind} for path, kind in entries]}
    if truncated is not None:
        payload["truncated"] = truncated
    return payload


def blobs(*paths: str, truncated: bool | None = False) -> dict:
    return tree(*((path, "blob") for path in paths), truncated=truncated)


class TestClassify(unittest.TestCase):
    def test_every_documented_signature_is_classified(self):
        cases = {
            "package.json": "npm",
            "package-lock.json": "npm",
            "pnpm-lock.yaml": "npm",
            "yarn.lock": "npm",
            "requirements.txt": "pip",
            "requirements-dev.txt": "pip",
            "requirements_test.txt": "pip",
            "Pipfile": "pip",
            "setup.py": "pip",
            "uv.lock": "uv",
            "pyproject.toml": "pip|uv",
            "Dockerfile": "docker",
            "Dockerfile.prod": "docker",
            "docker-compose.yml": "docker-compose",
            "docker-compose.override.yaml": "docker-compose",
            "go.mod": "gomod",
            "Gemfile": "bundler",
            "Cargo.toml": "cargo",
            "composer.json": "composer",
            "Api.csproj": "nuget",
            "packages.config": "nuget",
            "global.json": "dotnet-sdk",
            "pom.xml": "maven",
            "build.gradle": "gradle",
            "build.gradle.kts": "gradle",
            "main.tf": "terraform|opentofu",
            "Chart.yaml": "helm",
            "mix.exs": "mix",
            "Package.swift": "swift",
            "pubspec.yaml": "pub",
            "bun.lock": "bun",
            "bun.lockb": "bun",
            "devcontainer.json": "devcontainers",
            ".devcontainer.json": "devcontainers",
            ".gitmodules": "gitsubmodule",
            ".pre-commit-config.yaml": "pre-commit",
            ".pre-commit-config.yml": "pre-commit",
        }
        for basename, expected in cases.items():
            with self.subTest(basename=basename):
                self.assertEqual(report.classify(basename), expected)

    def test_signature_table_matches_the_reference_doc(self):
        # The classifier mirrors the ecosystem table in
        # reference/dependabot-config.md. Parse it so the two cannot drift.
        doc = (
            Path(__file__).resolve().parent.parent
            / "reference"
            / "dependabot-config.md"
        ).read_text()

        lines = doc.splitlines()
        header = next(
            i
            for i, line in enumerate(lines)
            if line.startswith("| Ecosystem") and "YAML Value" in line
        )
        documented = set()
        for line in lines[header + 2 :]:
            if not line.startswith("|"):
                break
            match = re.match(r"\|[^|]+\|\s*`([a-z-]+)`", line)
            if match:
                documented.add(match.group(1))

        implemented = {"github-actions"}
        for _, value in report.ECOSYSTEM_SIGNATURES:
            implemented.update(value.split("|"))

        self.assertEqual(documented, implemented)
        self.assertEqual(len(documented), 24)

    def test_unrelated_files_are_not_classified(self):
        for basename in ("README.md", "main.go", "index.ts", "LICENSE", "tsconfig.json"):
            with self.subTest(basename=basename):
                self.assertIsNone(report.classify(basename))

    def test_prefix_lookalikes_are_rejected(self):
        # "^Dockerfile" and "requirements.*\.txt" used to match these.
        self.assertIsNone(report.classify("DockerfileTemplate.txt"))
        self.assertIsNone(report.classify("requirementsfoo.txt"))

    def test_submodule_pointers_classify_regardless_of_name(self):
        self.assertEqual(report.classify("vendor/lib", "commit"), "gitsubmodule")

    def test_workflows_and_composite_actions_are_github_actions(self):
        for path in (
            ".github/workflows/ci.yml",
            ".github/workflows/release.yaml",
            "action.yml",
            "action.yaml",
            "actions/setup/action.yml",
        ):
            with self.subTest(path=path):
                self.assertEqual(report.classify(path), "github-actions")

    def test_nested_workflow_directories_are_not_workflows(self):
        # Dependabot only reads .github/workflows/*.yml, not deeper nesting.
        self.assertIsNone(report.classify(".github/workflows/nested/ci.yml"))


class TestDirectoryRules(unittest.TestCase):
    def test_devcontainer_directory_is_the_project_root(self):
        cases = {
            ".devcontainer/devcontainer.json": "/",
            ".devcontainer/backend/devcontainer.json": "/",
            ".devcontainer.json": "/",
            "extensions/copilot/.devcontainer/devcontainer.json": "/extensions/copilot",
            "apps/web/.devcontainer/web/devcontainer.json": "/apps/web",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(
                    report.directory_for(path, "devcontainers"), expected
                )

    def test_devcontainer_directory_is_never_the_devcontainer_folder(self):
        self.assertNotEqual(
            report.directory_for(".devcontainer/devcontainer.json", "devcontainers"),
            "/.devcontainer",
        )

    def test_workflows_register_at_the_repo_root(self):
        self.assertEqual(
            report.directory_for(".github/workflows/ci.yml", "github-actions"), "/"
        )

    def test_composite_actions_register_at_their_own_folder(self):
        # The inverse of the devcontainers rule.
        self.assertEqual(report.directory_for("action.yml", "github-actions"), "/")
        self.assertEqual(
            report.directory_for("actions/setup/action.yml", "github-actions"),
            "/actions/setup",
        )

    def test_submodules_register_in_the_superproject_root(self):
        self.assertEqual(
            report.directory_for("vendor/lib", "gitsubmodule", "commit"), "/"
        )

    def test_ordinary_manifests_use_their_own_folder(self):
        self.assertEqual(report.directory_for("package.json", "npm"), "/")
        self.assertEqual(report.directory_for("apps/web/package.json", "npm"), "/apps/web")


class TestCandidateOnly(unittest.TestCase):
    def test_vendored_and_fixture_directories_are_candidates(self):
        for directory in (
            "/node_modules/left-pad",
            "/vendor",
            "/vendor/github.com/pkg",
            "/third_party/zlib",
            "/testdata",
            "/test/fixtures/sample",
        ):
            with self.subTest(directory=directory):
                self.assertTrue(report.is_candidate_only(directory))

    def test_partial_segment_matches_are_not_candidates(self):
        for directory in ("/", "/src/vendor-utils", "/apps/web", "/vendored-libs"):
            with self.subTest(directory=directory):
                self.assertFalse(report.is_candidate_only(directory))


class TestBuildInventory(unittest.TestCase):
    def test_groups_paths_into_one_entry_per_ecosystem_and_directory(self):
        result = report.build_inventory(
            blobs(
                ".github/workflows/ci.yml",
                ".github/workflows/release.yml",
                "action.yml",
                "package.json",
            ),
            "main",
            "abc123",
        )
        self.assertTrue(result["ok"])
        actions = [e for e in result["entries"] if e["ecosystem"] == "github-actions"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["directory"], "/")
        self.assertEqual(
            actions[0]["paths"],
            [".github/workflows/ci.yml", ".github/workflows/release.yml", "action.yml"],
        )

    def test_nested_composite_action_is_a_separate_entry(self):
        result = report.build_inventory(
            blobs(".github/workflows/ci.yml", "actions/setup/action.yml"), "main", "s"
        )
        directories = sorted(
            e["directory"] for e in result["entries"] if e["ecosystem"] == "github-actions"
        )
        self.assertEqual(directories, ["/", "/actions/setup"])

    def test_devcontainer_is_detected_and_rooted(self):
        # The original reported failure: a devcontainer that went unnoticed.
        result = report.build_inventory(
            blobs(".devcontainer/devcontainer.json"), "main", "s"
        )
        self.assertEqual(
            result["entries"],
            [
                {
                    "ecosystem": "devcontainers",
                    "directory": "/",
                    "paths": [".devcontainer/devcontainer.json"],
                    "ambiguous": False,
                    "candidate_only": False,
                }
            ],
        )

    def test_submodule_under_vendor_is_not_flagged_as_a_candidate(self):
        result = report.build_inventory(
            tree((".gitmodules", "blob"), ("vendor/lib", "commit")), "main", "s"
        )
        entry = result["entries"][0]
        self.assertEqual(entry["ecosystem"], "gitsubmodule")
        self.assertEqual(entry["directory"], "/")
        self.assertFalse(entry["candidate_only"])
        self.assertEqual(entry["paths"], [".gitmodules", "vendor/lib"])

    def test_vendored_manifests_are_flagged_but_still_reported(self):
        result = report.build_inventory(blobs("node_modules/dep/package.json"), "m", "s")
        self.assertTrue(result["entries"][0]["candidate_only"])

    def test_ambiguous_signatures_are_marked(self):
        result = report.build_inventory(blobs("pyproject.toml", "uv.lock"), "m", "s")
        by_eco = {e["ecosystem"]: e for e in result["entries"]}
        self.assertTrue(by_eco["pip|uv"]["ambiguous"])
        self.assertFalse(by_eco["uv"]["ambiguous"])

    def test_entries_are_sorted_for_stable_output(self):
        result = report.build_inventory(
            blobs("apps/web/package.json", "Dockerfile", "go.mod"), "m", "s"
        )
        keys = [(e["ecosystem"], e["directory"]) for e in result["entries"]]
        self.assertEqual(keys, sorted(keys))

    def test_unrecognised_files_are_ignored(self):
        result = report.build_inventory(blobs("README.md", "src/main.go"), "m", "s")
        self.assertEqual(result["entries"], [])
        self.assertTrue(result["ok"])

    def test_directory_entries_are_ignored(self):
        result = report.build_inventory(tree(("src", "tree")), "m", "s")
        self.assertEqual(result["entries"], [])


class TestInventoryFailsClosed(unittest.TestCase):
    def test_complete_tree_is_ok(self):
        result = report.build_inventory(blobs("go.mod", truncated=False), "main", "s")
        self.assertTrue(result["ok"])
        self.assertIsNone(result["error"])

    def test_truncated_tree_is_not_ok_but_keeps_partial_evidence(self):
        result = report.build_inventory(blobs("go.mod", truncated=True), "main", "s")
        self.assertFalse(result["ok"])
        self.assertIn("truncated", result["error"])
        self.assertEqual(len(result["entries"]), 1)

    def test_missing_truncated_flag_is_not_ok(self):
        result = report.build_inventory(blobs("go.mod", truncated=None), "main", "s")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], report.UNKNOWN_SHAPE_ERROR)

    def test_non_boolean_truncated_flag_is_not_ok(self):
        payload = blobs("go.mod")
        payload["truncated"] = "false"
        self.assertFalse(report.build_inventory(payload, "main", "s")["ok"])

    def test_unexpected_response_shape_is_not_ok(self):
        for payload in (None, [], {"message": "Not Found"}, "nope"):
            with self.subTest(payload=payload):
                result = report.build_inventory(payload, None, None)
                self.assertFalse(result["ok"])
                self.assertEqual(result["entries"], [])


class TestAlertSummary(unittest.TestCase):
    def alert(self, state, package="left-pad", severity="high"):
        return {
            "number": 1,
            "state": state,
            "security_advisory": {"severity": severity, "summary": "bad"},
            "dependency": {
                "package": {"name": package, "ecosystem": "npm"},
                "manifest_path": "package.json",
            },
            "html_url": "https://example.test/1",
            "created_at": "2024-01-01T00:00:00Z",
            "fixed_at": None,
            "auto_dismissed_at": None,
        }

    def test_only_open_alerts_are_listed(self):
        result = report.summarize_alerts(
            [self.alert("open"), self.alert("fixed")], include_closed=False
        )
        self.assertEqual(len(result["open"]), 1)
        self.assertIsNone(result["closed_summary"])

    def test_closed_rollup_counts_by_state_and_package(self):
        alerts = [
            self.alert("open"),
            self.alert("fixed", "lodash"),
            self.alert("fixed", "lodash"),
            self.alert("dismissed", "minimist"),
            self.alert("auto_dismissed", "minimist"),
        ]
        summary = report.summarize_alerts(alerts, include_closed=True)["closed_summary"]
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["fixed"], 2)
        self.assertEqual(summary["dismissed"], 2)
        self.assertEqual(summary["by_package"][0], {"package": "lodash", "count": 2})

    def test_missing_nested_fields_do_not_raise(self):
        result = report.summarize_alerts([{"state": "open"}], include_closed=True)
        self.assertIsNone(result["open"][0]["severity"])
        self.assertIsNone(result["open"][0]["package"])


class TestPullRequestSummary(unittest.TestCase):
    def pr(self, state, title="build(deps): bump lodash from 1 to 2", rollup=None):
        return {
            "number": 7,
            "title": title,
            "url": "https://example.test/7",
            "state": state,
            "headRefName": "dependabot/npm_and_yarn/lodash-2",
            "createdAt": "2024-01-01T00:00:00Z",
            "closedAt": None,
            "statusCheckRollup": rollup,
        }

    def test_only_open_prs_are_listed(self):
        result = report.summarize_prs(
            [self.pr("OPEN"), self.pr("MERGED")], include_closed=False
        )
        self.assertEqual(len(result["open"]), 1)

    def test_closed_rollup_splits_merged_from_closed(self):
        prs = [self.pr("MERGED"), self.pr("MERGED"), self.pr("CLOSED")]
        summary = report.summarize_prs(prs, include_closed=True)["closed_summary"]
        self.assertEqual((summary["total"], summary["merged"]), (3, 2))
        self.assertEqual(summary["closed_unmerged"], 1)
        self.assertEqual(summary["by_package"][0], {"package": "lodash", "count": 3})

    def test_dependency_name_falls_back_to_the_title(self):
        self.assertEqual(report._dependency_name("chore(deps-dev): bump jest from 1 to 2"), "jest")
        self.assertEqual(report._dependency_name("Update things"), "Update things")

    def test_ci_status_prefers_conclusion_and_is_deduplicated(self):
        rollup = [
            {"conclusion": "SUCCESS"},
            {"conclusion": "SUCCESS"},
            {"conclusion": None, "state": "PENDING"},
        ]
        self.assertEqual(report._ci_status(rollup), "PENDING,SUCCESS")

    def test_ci_status_handles_a_missing_rollup(self):
        self.assertEqual(report._ci_status(None), "")


class TestSectionsFailClosed(unittest.TestCase):
    """A failed fetch must never be indistinguishable from an empty result."""

    def test_alert_fetch_failure_is_not_zero_alerts(self):
        with mock.patch.object(
            report, "run_gh", side_effect=report.GitHubError("HTTP 403")
        ):
            result = report.fetch_alerts("o/r", include_closed=False)
        self.assertFalse(result["ok"])
        self.assertIn("403", result["error"])
        self.assertEqual(result["open"], [])

    def test_pr_fetch_failure_is_reported(self):
        with mock.patch.object(
            report, "run_gh", side_effect=report.GitHubError("boom")
        ):
            self.assertFalse(report.fetch_prs("o/r", include_closed=False)["ok"])

    def test_metadata_fetch_failure_is_reported(self):
        with mock.patch.object(
            report, "run_gh", side_effect=report.GitHubError("boom")
        ):
            self.assertFalse(report.fetch_metadata("o/r")["ok"])

    def test_missing_config_is_absent_not_an_error(self):
        with mock.patch.object(
            report, "run_gh", side_effect=report.GitHubError("HTTP 404: Not Found")
        ):
            result = report.fetch_config("o/r")
        self.assertTrue(result["ok"])
        self.assertFalse(result["present"])

    def test_unreadable_config_is_an_error_not_an_absence(self):
        with mock.patch.object(
            report, "run_gh", side_effect=report.GitHubError("HTTP 403")
        ):
            result = report.fetch_config("o/r")
        self.assertFalse(result["ok"])
        self.assertIsNone(result["present"])

    def test_config_is_found_under_either_extension(self):
        import base64

        encoded = base64.b64encode(b"version: 2\n").decode()
        for path in report.CONFIG_PATHS:
            with self.subTest(path=path):

                def fake(args, wanted=path):
                    if wanted in args[1]:
                        return {"content": encoded, "encoding": "base64"}
                    raise report.GitHubError("HTTP 404: Not Found")

                with mock.patch.object(report, "run_gh", side_effect=fake):
                    result = report.fetch_config("o/r")
                self.assertTrue(result["ok"])
                self.assertEqual(result["path"], path)
                self.assertEqual(result["raw"], "version: 2\n")

    def test_contents_response_without_content_is_not_an_absence(self):
        with mock.patch.object(report, "run_gh", return_value={"encoding": "none"}):
            result = report.fetch_config("o/r")
        self.assertFalse(result["ok"])
        self.assertIsNone(result["present"])

    def test_unresolvable_default_branch_yields_no_false_absence(self):
        with mock.patch.object(
            report, "run_gh", side_effect=report.GitHubError("HTTP 404")
        ):
            result = report.fetch_manifests("o/r")
        self.assertFalse(result["ok"])
        self.assertEqual(result["entries"], [])


class TestRepoReport(unittest.TestCase):
    def test_repo_ok_requires_every_section_to_be_ok(self):
        healthy = report.section(True, None)
        with mock.patch.multiple(
            report,
            fetch_metadata=mock.Mock(return_value=healthy),
            fetch_alerts=mock.Mock(return_value=report.section(False, "403")),
            fetch_prs=mock.Mock(return_value=healthy),
            fetch_config=mock.Mock(return_value=healthy),
            fetch_manifests=mock.Mock(return_value=healthy),
        ):
            result = report.report_for_repo("o/r", False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["repo"], "o/r")

    def test_one_failing_repo_does_not_abort_the_run(self):
        def flaky(repo, include_closed):
            if repo == "o/bad":
                raise RuntimeError("network gone")
            return {"repo": repo, "ok": True}

        with mock.patch.object(report, "report_for_repo", side_effect=flaky):
            code, out, _ = run_cli(["o/bad", "o/good", "--quiet"])

        self.assertEqual(code, report.EXIT_OK)
        self.assertEqual([r["ok"] for r in json.loads(out)], [False, True])


def run_cli(argv):
    """Invoke main() with gh present, capturing stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(report.shutil, "which", return_value="/usr/bin/gh"), \
         contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = report.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    """The CLI surface an agent reads: exit codes, stderr, and output size."""

    def ok_report(self, repo="o/r", entries=1):
        return {
            "repo": repo,
            "ok": True,
            "manifest_inventory": {
                "ok": True,
                "entries": [
                    {"ecosystem": "npm", "directory": f"/p{i}"} for i in range(entries)
                ],
            },
        }

    def test_malformed_repo_is_rejected_before_any_api_call(self):
        with mock.patch.object(report, "report_for_repo") as fetch:
            code, _, err = run_cli(["not-a-slug"])
        fetch.assert_not_called()
        self.assertEqual(code, report.EXIT_USAGE)
        self.assertIn("owner/repo", err)
        self.assertIn("not-a-slug", err)

    def test_accepts_names_with_dots_and_dashes(self):
        for repo in ("o/r", "my-org/my.repo", "a_b/c-d.e"):
            with self.subTest(repo=repo):
                self.assertTrue(report.REPO_ARG.match(repo))
        for bad in ("bare", "a/b/c", "o/", "/r", "o r"):
            with self.subTest(bad=bad):
                self.assertFalse(report.REPO_ARG.match(bad))

    def test_missing_gh_reports_prereq_and_says_how_to_fix_it(self):
        err_buf = io.StringIO()
        with mock.patch.object(report.shutil, "which", return_value=None), \
             contextlib.redirect_stderr(err_buf):
            code = report.main(["o/r"])
        self.assertEqual(code, report.EXIT_PREREQ)
        self.assertIn("cli.github.com", err_buf.getvalue())

    def test_all_repos_failing_exits_no_report(self):
        def boom(repo, include_closed):
            raise RuntimeError("network gone")

        with mock.patch.object(report, "report_for_repo", side_effect=boom):
            code, out, err = run_cli(["o/a", "o/b", "--quiet"])
        self.assertEqual(code, report.EXIT_NO_REPORT)
        self.assertIn("gh auth status", err)
        # The payload is still emitted so the caller can read the reasons.
        self.assertEqual(len(json.loads(out)), 2)

    def test_partial_success_still_exits_zero(self):
        def flaky(repo, include_closed):
            if repo == "o/bad":
                raise RuntimeError("nope")
            return self.ok_report(repo)

        with mock.patch.object(report, "report_for_repo", side_effect=flaky):
            code, _, _ = run_cli(["o/bad", "o/good", "--quiet"])
        self.assertEqual(code, report.EXIT_OK)

    def test_large_stdout_payload_warns_about_truncation(self):
        big = self.ok_report(entries=4000)
        with mock.patch.object(report, "report_for_repo", return_value=big):
            _, out, err = run_cli(["o/r", "--quiet"])
        self.assertGreater(len(out), report.STDOUT_WARN_CHARS)
        self.assertIn("truncated", err)
        self.assertIn("--output", err)

    def test_small_payload_does_not_warn(self):
        with mock.patch.object(report, "report_for_repo", return_value=self.ok_report()):
            _, _, err = run_cli(["o/r", "--quiet"])
        self.assertNotIn("truncated", err)

    def test_output_file_keeps_stdout_small_and_writes_full_json(self):
        big = self.ok_report(entries=4000)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "report.json")
            with mock.patch.object(report, "report_for_repo", return_value=big):
                code, out, _ = run_cli(["o/r", "--output", path, "--quiet"])
            self.assertEqual(code, report.EXIT_OK)
            written = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(len(written[0]["manifest_inventory"]["entries"]), 4000)
        # stdout carries a summary, not the payload.
        self.assertLess(len(out), 500)
        self.assertIn(path, out)

    def test_unwritable_output_path_is_a_usage_error(self):
        with mock.patch.object(report, "report_for_repo", return_value=self.ok_report()):
            code, _, err = run_cli(["o/r", "--output", "/nope/nope.json", "--quiet"])
        self.assertEqual(code, report.EXIT_USAGE)
        self.assertIn("could not write", err)

    def test_stdout_stays_pure_json_while_diagnostics_go_to_stderr(self):
        with mock.patch.object(report, "report_for_repo", return_value=self.ok_report()):
            _, out, err = run_cli(["o/r"])
        json.loads(out)  # would raise if progress lines leaked into stdout
        self.assertIn("[1/1] o/r", err)

    def test_quiet_suppresses_progress(self):
        with mock.patch.object(report, "report_for_repo", return_value=self.ok_report()):
            _, _, err = run_cli(["o/r", "--quiet"])
        self.assertEqual(err, "")

    def test_summary_names_the_unreadable_sections(self):
        degraded = {
            "repo": "o/r",
            "ok": False,
            "alerts": {"ok": False, "error": "403"},
            "manifest_inventory": {"ok": True, "entries": []},
        }
        line = report.summarize_report(degraded)
        self.assertIn("degraded", line)
        self.assertIn("alerts", line)


class TestRunGh(unittest.TestCase):
    def gh(self, stdout="", stderr="", code=0):
        return mock.patch.object(
            report.subprocess,
            "run",
            return_value=mock.Mock(returncode=code, stdout=stdout, stderr=stderr),
        )

    def test_parses_a_single_document(self):
        with self.gh(stdout='{"default_branch": "main"}'):
            self.assertEqual(report.run_gh(["api", "repos/o/r"]), {"default_branch": "main"})

    def test_flattens_concatenated_pages(self):
        with self.gh(stdout='[{"number": 1}]\n[{"number": 2}]'):
            self.assertEqual(
                report.run_gh(["api", "x", "--paginate"]),
                [{"number": 1}, {"number": 2}],
            )

    def test_flattens_pages_containing_nested_arrays(self):
        # Splitting on brackets mis-parses this; a streaming decoder does not.
        page = '[{"checks": [1, 2]}]'
        with self.gh(stdout=f"{page}{page}"):
            self.assertEqual(
                report.run_gh(["api", "x", "--paginate"]),
                [{"checks": [1, 2]}, {"checks": [1, 2]}],
            )

    def test_nonzero_exit_raises_with_the_reported_reason(self):
        # gh writes the API error body to stdout, so exit status decides.
        with self.gh(stdout='{"message": "Not Found"}', stderr="gh: HTTP 404", code=1):
            with self.assertRaises(report.GitHubError) as caught:
                report.run_gh(["api", "x"])
        self.assertIn("404", str(caught.exception))

    def test_empty_output_raises(self):
        with self.gh(stdout="  "):
            with self.assertRaises(report.GitHubError):
                report.run_gh(["api", "x"])

    def test_unparseable_output_raises(self):
        with self.gh(stdout="not json at all"):
            with self.assertRaises(report.GitHubError):
                report.run_gh(["api", "x"])


class TestNormalizeRepo(unittest.TestCase):
    def test_flattens_nested_gh_fields(self):
        result = report.normalize_repo(
            {
                "name": "r",
                "nameWithOwner": "o/r",
                "defaultBranchRef": {"name": "main"},
                "primaryLanguage": {"name": "Go"},
                "languages": [{"node": {"name": "Go"}}, {"node": {"name": "Shell"}}],
                "owner": {"login": "o"},
            }
        )
        self.assertEqual(result["default_branch"], "main")
        self.assertEqual(result["primary_language"], "Go")
        self.assertEqual(result["languages"], ["Go", "Shell"])
        self.assertEqual(result["owner"], "o")

    def test_tolerates_missing_nested_objects(self):
        result = report.normalize_repo({})
        self.assertIsNone(result["default_branch"])
        self.assertEqual(result["languages"], [])


if __name__ == "__main__":
    unittest.main()
