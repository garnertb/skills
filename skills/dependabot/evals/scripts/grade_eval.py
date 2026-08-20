#!/usr/bin/env python3
"""Grade one Dependabot skill eval output.

Produces benchmark-friendly output with `expectations` entries that include:
- text
- passed
- evidence
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXPECTATIONS = {
    0: [
        {
            "text": "Recommends /dependabot report as top next step",
            "required": [r"/dependabot\s+report", r"recommend|top"],
            "forbidden": [],
        },
        {
            "text": "Does not auto-run a command",
            "required": [r"confirm|choose|pick"],
            "forbidden": [r"i ran|running\s+/dependabot|executed\s+/dependabot"],
        },
        {
            "text": "Mentions menu is context-aware",
            "required": [r"context-aware|based on.*context|menu"],
            "forbidden": [],
        },
    ],
    1: [
        {
            "text": "Includes alerts, PRs, and dependabot config",
            "required": [
                r"alert",
                r"pull request|\bpr\b",
                r"dependabot\.yml|dependabot config",
            ],
            "forbidden": [],
        },
        {
            "text": "Calls out archived repo behavior as stale/frozen data",
            "required": [r"archived", r"stale|frozen|not current"],
            "forbidden": [],
        },
        {
            "text": "Flags missing ecosystem coverage",
            "required": [r"missing", r"ecosystem|language"],
            "forbidden": [],
        },
        {
            "text": "References closed summary when asked for closed history",
            "required": [r"closed_summary|closed summary|merged|dismissed|fixed"],
            "forbidden": [],
        },
        {
            "text": "Report stands alone without a redundant recap or meta-commentary",
            "required": [],
            "forbidden": [
                r"key findings:",
                r"recommendations given",
                r"report is delivered|report has been delivered|delivered the (?:dependabot )?report",
                r"analyze-only command",
            ],
        },
    ],
    2: [
        {
            "text": "Uses a four-tier risk model",
            "required": [r"tier\s*0", r"tier\s*1", r"tier\s*2", r"tier\s*3"],
            "forbidden": [],
        },
        {
            "text": "Performs changelog/release-note analysis for high-risk updates",
            "required": [r"changelog|release", r"breaking|migration"],
            "forbidden": [],
        },
        {
            "text": "Performs integration-point analysis for high-risk updates",
            "required": [r"integration", r"import|usage|critical path|test coverage"],
            "forbidden": [],
        },
        {
            "text": "Defines execution strategy and validation depth",
            "required": [r"strategy|fast-track|batch|defer", r"validation|rollout|rollback"],
            "forbidden": [],
        },
        {
            "text": "Includes guardrail against blind auto-merge of risky updates",
            "required": [r"do not|avoid", r"auto-merge", r"tier\s*0|tier\s*1|high-risk"],
            "forbidden": [],
        },
    ],
    3: [
        {
            "text": "States dependabot uses a single config file",
            "required": [r"single", r"\.github/dependabot\.yml|dependabot\.yml"],
            "forbidden": [r"multiple.*dependabot\.yml.*supported"],
        },
        {
            "text": "Rejects blanket auto-merge for major/risky updates",
            "required": [r"do not|avoid|shouldn'?t", r"auto-merge", r"major|risky|high-risk"],
            "forbidden": [],
        },
    ],
    4: [
        {
            "text": "Flags missing github-actions ecosystem coverage",
            "required": [r"github-actions", r"missing|not (?:configured|covered)|gap"],
            "forbidden": [],
        },
        {
            "text": "Proposes directories globs for monorepo coverage",
            "required": [r"directories", r"apps/\*|packages/\*|glob"],
            "forbidden": [],
        },
        {
            "text": "Recommends grouping to reduce PR noise",
            "required": [r"group|groups"],
            "forbidden": [],
        },
        {
            "text": "Confirms plan before writing dependabot.yml",
            "required": [r"confirm|before (?:writing|applying|updating)|approve"],
            "forbidden": [],
        },
    ],
    5: [
        {
            "text": "Scans the remote repo's full file tree rather than assuming a local checkout",
            "required": [r"git/trees|recursive=1", r"gh api|api\.github\.com"],
            "forbidden": [],
        },
        {
            "text": "Pins the scan to a resolved default branch or commit SHA",
            "required": [r"default[ -]branch|commit sha|\bsha\b|\bref\b"],
            "forbidden": [],
        },
        {
            "text": "Handles truncated or failed acquisition fail-closed",
            "required": [
                r"truncat",
                r"incomplete|fail|cannot|unable|do(?:es)?n['’]?t (?:conclude|report)",
            ],
            "forbidden": [],
        },
        {
            "text": "Reports scan source and completeness",
            "required": [r"scan|inventory", r"complete|truncat|partial"],
            "forbidden": [],
        },
        {
            "text": "Surfaces hidden-path ecosystems rather than inferring from the language list",
            "required": [r"\.devcontainer|\.gitmodules|\.pre-commit|\.github/workflows"],
            "forbidden": [],
        },
    ],
    6: [
        {
            "text": "Identifies the devcontainers ecosystem from the raw file listing",
            "required": [r"devcontainers"],
            "forbidden": [],
        },
        {
            "text": "Uses the project root as the devcontainers directory, not the .devcontainer folder",
            "required": [
                r"package-ecosystem:\s*[\"']devcontainers[\"'][\s\S]{0,120}?directory:\s*[\"']/[\"']"
            ],
            "forbidden": [
                r"package-ecosystem:\s*[\"']devcontainers[\"'][\s\S]{0,120}?directory:\s*[\"']?/?\.devcontainer"
            ],
        },
        {
            "text": "Maps the nested devcontainer to its containing project root",
            "required": [
                r"package-ecosystem:\s*[\"']devcontainers[\"'][\s\S]{0,160}?directory:\s*[\"']/services/worker[\"']"
            ],
            "forbidden": [
                r"directory:\s*[\"']/services/worker/\.devcontainer"
            ],
        },
        {
            "text": "Flags gitsubmodule and github-actions from hidden paths",
            "required": [r"gitsubmodule", r"github-actions"],
            "forbidden": [],
        },
        {
            "text": "Chooses uv over pip because uv.lock is present",
            "required": [r"\buv\b", r"uv\.lock"],
            "forbidden": [],
        },
        {
            "text": "Treats the test fixture devcontainer as a candidate needing confirmation",
            "required": [r"test/fixtures|fixture", r"confirm|candidate|exclude|skip"],
            "forbidden": [],
        },
    ],
}


def _load_eval_ids(evals_path: Path) -> set[int]:
    data = json.loads(evals_path.read_text(encoding="utf-8"))
    return {int(item["id"]) for item in data.get("evals", [])}


def _check_patterns(text: str, patterns: list[str]) -> tuple[bool, list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            matched.append(pattern)
        else:
            missing.append(pattern)
    return (len(missing) == 0, matched, missing)


def grade(eval_id: int, output_text: str) -> dict:
    rules = EXPECTATIONS.get(eval_id)
    if not rules:
        raise ValueError(f"No expectations configured for eval_id={eval_id}")

    expectations = []
    passed_count = 0

    for rule in rules:
        required_ok, req_matched, req_missing = _check_patterns(
            output_text, rule.get("required", [])
        )
        forbidden_hit: list[str] = []
        for pattern in rule.get("forbidden", []):
            if re.search(pattern, output_text, flags=re.IGNORECASE | re.DOTALL):
                forbidden_hit.append(pattern)

        passed = required_ok and not forbidden_hit
        if passed:
            passed_count += 1

        evidence_parts = []
        if req_matched:
            evidence_parts.append("required matched: " + ", ".join(req_matched))
        if req_missing:
            evidence_parts.append("required missing: " + ", ".join(req_missing))
        if forbidden_hit:
            evidence_parts.append("forbidden matched: " + ", ".join(forbidden_hit))
        if not evidence_parts:
            evidence_parts.append("no evidence")

        expectations.append(
            {
                "text": rule["text"],
                "passed": passed,
                "evidence": " | ".join(evidence_parts),
            }
        )

    return {
        "eval_id": eval_id,
        "expectations": expectations,
        "summary": {"passed": passed_count, "total": len(expectations)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade a single dependabot skill eval output")
    parser.add_argument("--evals", required=True, help="Path to evals.json")
    parser.add_argument("--eval-id", required=True, type=int, help="Eval id from evals.json")
    parser.add_argument("--output", required=True, help="Path to model output text/markdown")
    parser.add_argument(
        "--write",
        default="",
        help="Optional output path for grading JSON. Prints to stdout when omitted.",
    )
    args = parser.parse_args()

    evals_path = Path(args.evals)
    output_path = Path(args.output)

    if not evals_path.exists():
        print(f"error: evals file not found: {evals_path}", file=sys.stderr)
        return 1
    if not output_path.exists():
        print(f"error: output file not found: {output_path}", file=sys.stderr)
        return 1

    eval_ids = _load_eval_ids(evals_path)
    if args.eval_id not in eval_ids:
        print(f"error: eval_id {args.eval_id} not present in {evals_path}", file=sys.stderr)
        return 1

    output_text = output_path.read_text(encoding="utf-8")
    result = grade(args.eval_id, output_text)

    payload = json.dumps(result, indent=2)
    if args.write:
        Path(args.write).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
