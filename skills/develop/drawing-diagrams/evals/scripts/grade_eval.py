#!/usr/bin/env python3
"""Grade one drawing-diagrams skill eval output.

Diagram outputs are SVG, so grading pairs text checks on the reply with
deterministic structural checks on the generated SVG. Each expectation reports
`text`, `passed`, and `evidence`, matching the benchmark shape used by the other
skills in this repo.

The grader gathers SVGs from two places, in order:
  1. every ``*.svg`` file under the output file's directory tree, and
  2. any ``<svg>...</svg>`` embedded in the reply markdown (fenced or inline).

Subjective qualities a parser cannot judge -- spacing, legibility, crossing
connectors -- are intentionally left to the human visual review step documented
in the eval README, not asserted here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Tolerance (in user units) for treating a path segment as axis-aligned, and for
# treating a rect as covering the full canvas. Diagrams are authored on a coarse
# integer grid, so a couple of units of slack absorbs rounding without masking a
# genuine diagonal.
AXIS_TOLERANCE = 1.5
FULL_CANVAS_FRACTION = 0.95

# Tokens that only appear with the decoration styles the skill forbids. Scanned
# case-insensitively against the raw SVG so inline styles are caught too.
DECORATION_TOKENS = (
    "lineargradient",
    "radialgradient",
    "<filter",
    "fedropshadow",
    "fegaussianblur",
    "drop-shadow",
    "box-shadow",
)


class Svg:
    """A parsed SVG plus its raw text, or a parse error."""

    def __init__(self, raw: str, source: str):
        self.raw = raw
        self.source = source
        self.root: ET.Element | None = None
        self.parse_error: str | None = None
        try:
            self.root = ET.fromstring(raw)
        except ET.ParseError as exc:
            self.parse_error = str(exc)

    def viewbox(self) -> tuple[float, float, float, float] | None:
        if self.root is None:
            return None
        vb = self.root.get("viewBox")
        if not vb:
            return None
        parts = re.split(r"[ ,]+", vb.strip())
        if len(parts) != 4:
            return None
        try:
            return tuple(float(p) for p in parts)  # type: ignore[return-value]
        except ValueError:
            return None


def _local(tag: str) -> str:
    """Strip the XML namespace from a tag, leaving the local element name."""
    return tag.rsplit("}", 1)[-1].lower()


def _walk(element: ET.Element, skip_tags: frozenset[str]):
    """Yield descendants of element, pruning entire skip_tags subtrees.

    Arrowhead markers live under <defs>/<marker> and are deliberately triangular,
    so connector-orthogonality checks must not see their diagonal paths.
    """
    for child in element:
        name = _local(child.tag)
        if name in skip_tags:
            continue
        yield child
        yield from _walk(child, skip_tags)


# --- SVG collection -----------------------------------------------------------


def collect_svgs(output_path: Path, response_text: str) -> list[Svg]:
    svgs: list[Svg] = []
    seen: set[str] = set()

    search_dir = output_path.parent
    for svg_file in sorted(search_dir.rglob("*.svg")):
        try:
            raw = svg_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if raw not in seen:
            seen.add(raw)
            svgs.append(Svg(raw, svg_file.name))

    for match in re.finditer(r"<svg\b[\s\S]*?</svg>", response_text, flags=re.IGNORECASE):
        raw = match.group(0)
        if raw not in seen:
            seen.add(raw)
            svgs.append(Svg(raw, "embedded-in-reply"))

    return svgs


# --- deterministic SVG checks -------------------------------------------------
# Each returns (passed, evidence). They pass only on positive evidence: with no
# SVG to inspect there is nothing to credit, so they fail closed.


def check_svg_present(svgs: list[Svg]) -> tuple[bool, str]:
    if not svgs:
        return False, "no SVG found in outputs or reply"
    return True, f"{len(svgs)} SVG(s): {', '.join(s.source for s in svgs)}"


def check_well_formed(svgs: list[Svg]) -> tuple[bool, str]:
    if not svgs:
        return False, "no SVG found"
    broken = [f"{s.source} ({s.parse_error})" for s in svgs if s.root is None]
    if broken:
        return False, "parse errors: " + "; ".join(broken)
    return True, "all SVG(s) are well-formed XML"


def check_transparent_background(svgs: list[Svg]) -> tuple[bool, str]:
    parsed = [s for s in svgs if s.root is not None]
    if not parsed:
        return False, "no parseable SVG found"
    for svg in parsed:
        vb = svg.viewbox()
        if vb is None:
            continue
        _, _, vw, vh = vb
        for rect in _walk(svg.root, frozenset({"defs"})):
            if _local(rect.tag) != "rect":
                continue
            fill = (rect.get("fill") or "").strip().lower()
            if fill in ("", "none", "transparent"):
                continue
            try:
                x = float(rect.get("x", "0"))
                y = float(rect.get("y", "0"))
                w = float(rect.get("width", "0"))
                h = float(rect.get("height", "0"))
            except ValueError:
                continue
            covers = (
                x <= AXIS_TOLERANCE
                and y <= AXIS_TOLERANCE
                and w >= FULL_CANVAS_FRACTION * vw
                and h >= FULL_CANVAS_FRACTION * vh
            )
            if covers:
                return False, f"{svg.source}: full-canvas rect fill '{fill}'"
    return True, "no full-canvas background fill"


def check_no_decoration(svgs: list[Svg]) -> tuple[bool, str]:
    if not svgs:
        return False, "no SVG found"
    for svg in svgs:
        lowered = svg.raw.lower()
        hits = [token for token in DECORATION_TOKENS if token in lowered]
        if hits:
            return False, f"{svg.source}: forbidden decoration {hits}"
    return True, "no gradients, filters, or shadows"


def check_vector_not_raster(svgs: list[Svg]) -> tuple[bool, str]:
    if not svgs:
        return False, "no SVG found"
    for svg in svgs:
        lowered = svg.raw.lower()
        if "<image" in lowered or "data:image/png" in lowered or "data:image/jpeg" in lowered:
            return False, f"{svg.source}: embeds raster image"
    return True, "vector-only, no embedded raster"


def _path_is_orthogonal(d: str) -> bool:
    """Whether a path's drawn segments are all horizontal or vertical.

    Any curve command (C/S/Q/T/A) is a diagonal by definition and fails. Line
    segments pass only when they move along a single axis within tolerance.
    """
    tokens = re.findall(r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+)", d)
    commands: list[tuple[str, list[float]]] = []
    current_cmd = ""
    numbers: list[float] = []
    for cmd, num in tokens:
        if cmd:
            if current_cmd:
                commands.append((current_cmd, numbers))
            current_cmd = cmd
            numbers = []
        else:
            numbers.append(float(num))
    if current_cmd:
        commands.append((current_cmd, numbers))

    x = y = 0.0
    started = False
    for cmd, nums in commands:
        upper = cmd.upper()
        relative = cmd.islower()
        if upper in ("C", "S", "Q", "T", "A"):
            return False
        if upper == "Z":
            continue
        if upper == "M":
            for i in range(0, len(nums) - 1, 2):
                nx, ny = nums[i], nums[i + 1]
                x, y = (x + nx, y + ny) if relative and started else (nx, ny)
                started = True
            continue
        if upper == "H":
            for nx in nums:
                x = x + nx if relative else nx
            continue
        if upper == "V":
            for ny in nums:
                y = y + ny if relative else ny
            continue
        if upper == "L":
            for i in range(0, len(nums) - 1, 2):
                nx, ny = nums[i], nums[i + 1]
                tx, ty = (x + nx, y + ny) if relative else (nx, ny)
                if abs(tx - x) > AXIS_TOLERANCE and abs(ty - y) > AXIS_TOLERANCE:
                    return False
                x, y = tx, ty
    return True


def _connector_paths(svg: Svg):
    """Paths that act as connectors: fill:none or carrying an arrowhead marker."""
    for path in _walk(svg.root, frozenset({"defs", "marker"})):
        if _local(path.tag) != "path":
            continue
        fill = (path.get("fill") or "").strip().lower()
        style = (path.get("style") or "").lower()
        is_connector = (
            fill == "none"
            or "fill:none" in style
            or path.get("marker-end")
            or path.get("marker-start")
        )
        if is_connector:
            yield path


def check_orthogonal_connectors(svgs: list[Svg]) -> tuple[bool, str]:
    parsed = [s for s in svgs if s.root is not None]
    if not parsed:
        return False, "no parseable SVG found"
    connectors = 0
    for svg in parsed:
        for path in _connector_paths(svg):
            d = path.get("d") or ""
            connectors += 1
            if not _path_is_orthogonal(d):
                return False, f"{svg.source}: non-orthogonal connector d='{d[:60]}'"
    if connectors == 0:
        return False, "no connector paths found to verify"
    return True, f"{connectors} connector(s) are all orthogonal"


def check_numbered_badges(svgs: list[Svg]) -> tuple[bool, str]:
    parsed = [s for s in svgs if s.root is not None]
    if not parsed:
        return False, "no parseable SVG found"
    for svg in parsed:
        has_circle = any(_local(e.tag) == "circle" for e in _walk(svg.root, frozenset()))
        digit_label = any(
            _local(e.tag) == "text" and (e.text or "").strip().isdigit()
            for e in _walk(svg.root, frozenset())
        )
        if has_circle and digit_label:
            return True, f"{svg.source}: numbered badges present"
    return False, "no circle + numeric label pairs found"


def check_swimlanes(svgs: list[Svg]) -> tuple[bool, str]:
    parsed = [s for s in svgs if s.root is not None]
    if not parsed:
        return False, "no parseable SVG found"
    for svg in parsed:
        if re.search(r"<!--\s*swimlane", svg.raw, flags=re.IGNORECASE):
            return True, f"{svg.source}: swimlane comment present"
        vb = svg.viewbox()
        if vb is None:
            continue
        _, _, vw, vh = vb
        bands = 0
        for rect in _walk(svg.root, frozenset({"defs"})):
            if _local(rect.tag) != "rect":
                continue
            try:
                w = float(rect.get("width", "0"))
                h = float(rect.get("height", "0"))
            except ValueError:
                continue
            if w >= 0.6 * vw or h >= 0.6 * vh:
                bands += 1
        if bands >= 2:
            return True, f"{svg.source}: {bands} band-like rects"
    return False, "no swimlane bands detected"


def check_multiple_diagrams(svgs: list[Svg]) -> tuple[bool, str]:
    if len(svgs) >= 2:
        return True, f"{len(svgs)} separate diagrams produced"
    return False, "only one diagram produced"


def _path_points(d: str) -> list[tuple[float, float]] | None:
    """Absolute points of an M/L/H/V path, or None if it contains a curve."""
    tokens = re.findall(r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+)", d)
    commands: list[tuple[str, list[float]]] = []
    current_cmd = ""
    numbers: list[float] = []
    for cmd, num in tokens:
        if cmd:
            if current_cmd:
                commands.append((current_cmd, numbers))
            current_cmd = cmd
            numbers = []
        else:
            numbers.append(float(num))
    if current_cmd:
        commands.append((current_cmd, numbers))

    points: list[tuple[float, float]] = []
    x = y = 0.0
    started = False
    for cmd, nums in commands:
        upper = cmd.upper()
        relative = cmd.islower()
        if upper in ("C", "S", "Q", "T", "A"):
            return None
        if upper == "Z":
            continue
        if upper == "M":
            for i in range(0, len(nums) - 1, 2):
                nx, ny = nums[i], nums[i + 1]
                x, y = (x + nx, y + ny) if relative and started else (nx, ny)
                started = True
                points.append((x, y))
        elif upper == "H":
            for nx in nums:
                x = x + nx if relative else nx
                points.append((x, y))
        elif upper == "V":
            for ny in nums:
                y = y + ny if relative else ny
                points.append((x, y))
        elif upper == "L":
            for i in range(0, len(nums) - 1, 2):
                nx, ny = nums[i], nums[i + 1]
                x, y = (x + nx, y + ny) if relative else (nx, ny)
                points.append((x, y))
    return points


def check_horizontal_timeline(svgs: list[Svg]) -> tuple[bool, str]:
    """Whether the layout reads as a left-to-right timeline.

    Passes on either positive signal: a dominant horizontal axis/connector
    spanning at least half the canvas width, or a row of three or more aligned
    node rects spread left-to-right across at least half the width.
    """
    parsed = [s for s in svgs if s.root is not None]
    if not parsed:
        return False, "no parseable SVG found"
    for svg in parsed:
        vb = svg.viewbox()
        if vb is None:
            continue
        _, _, vw, vh = vb

        for path in _connector_paths(svg):
            pts = _path_points(path.get("d") or "")
            if not pts:
                continue
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                if abs(ay - by) <= AXIS_TOLERANCE and abs(bx - ax) >= 0.5 * vw:
                    return True, f"{svg.source}: horizontal axis spanning {abs(bx - ax):.0f}u"

        centers_x: list[float] = []
        centers_y: list[float] = []
        for rect in _walk(svg.root, frozenset({"defs"})):
            if _local(rect.tag) != "rect":
                continue
            try:
                x = float(rect.get("x", "0"))
                y = float(rect.get("y", "0"))
                w = float(rect.get("width", "0"))
                h = float(rect.get("height", "0"))
            except ValueError:
                continue
            # Node-sized rects only: skip badge/legend swatches and swimlane bands.
            if w < 60 or h < 30 or w >= 0.6 * vw:
                continue
            centers_x.append(x + w / 2)
            centers_y.append(y + h / 2)
        if len(centers_x) >= 3:
            x_span = max(centers_x) - min(centers_x)
            y_spread = max(centers_y) - min(centers_y)
            if x_span >= 0.5 * vw and y_spread <= 0.25 * vh:
                return True, f"{svg.source}: {len(centers_x)} nodes in a left-to-right row"
    return False, "no horizontal timeline axis or node row detected"


SVG_CHECKS = {
    "svg_present": check_svg_present,
    "well_formed": check_well_formed,
    "transparent_background": check_transparent_background,
    "no_decoration": check_no_decoration,
    "vector_not_raster": check_vector_not_raster,
    "orthogonal_connectors": check_orthogonal_connectors,
    "numbered_badges": check_numbered_badges,
    "swimlanes": check_swimlanes,
    "multiple_diagrams": check_multiple_diagrams,
    "horizontal_timeline": check_horizontal_timeline,
}


# --- expectations -------------------------------------------------------------
# kind "svg" runs a deterministic check above; kind "text" runs required/forbidden
# regex against the reply markdown.

EXPECTATIONS = {
    0: [
        {"kind": "svg", "check": "well_formed", "text": "Produces a well-formed SVG"},
        {"kind": "svg", "check": "transparent_background", "text": "Background is transparent"},
        {"kind": "svg", "check": "no_decoration", "text": "No gradients, shadows, or 3D effects"},
        {"kind": "svg", "check": "vector_not_raster", "text": "Vector SVG, not raster"},
        {"kind": "svg", "check": "orthogonal_connectors", "text": "Connectors are orthogonal"},
        {
            "kind": "text",
            "text": "Reply reports the saved .svg path",
            "required": [r"\.svg"],
            "forbidden": [],
        },
    ],
    1: [
        {"kind": "svg", "check": "well_formed", "text": "Produces a well-formed SVG"},
        {"kind": "svg", "check": "numbered_badges", "text": "Numbers steps with badges"},
        {"kind": "svg", "check": "orthogonal_connectors", "text": "Connectors are orthogonal"},
        {"kind": "svg", "check": "transparent_background", "text": "Background is transparent"},
    ],
    2: [
        {"kind": "svg", "check": "well_formed", "text": "Produces a well-formed SVG"},
        {"kind": "svg", "check": "swimlanes", "text": "Uses labeled swimlanes for the actors"},
        {"kind": "svg", "check": "orthogonal_connectors", "text": "Connectors are orthogonal"},
    ],
    3: [
        {"kind": "svg", "check": "no_decoration", "text": "Refuses gradients and drop shadows"},
        {"kind": "svg", "check": "vector_not_raster", "text": "Delivers a flat vector SVG"},
        {
            "kind": "text",
            "text": "Notes the style constraint rather than silently complying",
            "required": [r"gradient|drop shadow|3d|flat|clean", r"instead|constraint|won'?t|cannot|avoid"],
            "forbidden": [],
        },
    ],
    4: [
        {"kind": "svg", "check": "multiple_diagrams", "text": "Splits into multiple diagrams"},
        {
            "kind": "text",
            "text": "Mentions splitting or high-level vs detail to avoid overcrowding",
            "required": [r"split|multiple diagrams|high-level|overview|detail|break (?:it|this) (?:up|down)"],
            "forbidden": [],
        },
    ],
    5: [
        {
            "kind": "text",
            "text": "Declines to write or refactor application code",
            "required": [r"only.*diagram|diagram.*only|do(?:es)?n'?t|won'?t|cannot|not.*(?:refactor|write.*code)"],
            "forbidden": [],
        },
        {"kind": "svg", "check": "well_formed", "text": "Still delivers the requested diagram"},
    ],
    6: [
        {"kind": "svg", "check": "well_formed", "text": "Produces a well-formed SVG"},
        {"kind": "svg", "check": "horizontal_timeline", "text": "Defaults to a left-to-right timeline layout"},
        {"kind": "svg", "check": "numbered_badges", "text": "Numbers the steps in order"},
        {"kind": "svg", "check": "orthogonal_connectors", "text": "Connectors are orthogonal"},
        {"kind": "svg", "check": "transparent_background", "text": "Background is transparent"},
    ],
}


def _check_text(text: str, rule: dict) -> tuple[bool, str]:
    required = rule.get("required", [])
    forbidden = rule.get("forbidden", [])
    missing = [p for p in required if not re.search(p, text, flags=re.IGNORECASE | re.DOTALL)]
    hit = [p for p in forbidden if re.search(p, text, flags=re.IGNORECASE | re.DOTALL)]
    passed = not missing and not hit
    parts = []
    if required and not missing:
        parts.append("required matched")
    if missing:
        parts.append("required missing: " + ", ".join(missing))
    if hit:
        parts.append("forbidden matched: " + ", ".join(hit))
    return passed, " | ".join(parts) or "no patterns configured"


def grade(eval_id: int, response_text: str, svgs: list[Svg]) -> dict:
    rules = EXPECTATIONS.get(eval_id)
    if not rules:
        raise ValueError(f"No expectations configured for eval_id={eval_id}")

    expectations = []
    passed_count = 0
    for rule in rules:
        if rule["kind"] == "svg":
            passed, evidence = SVG_CHECKS[rule["check"]](svgs)
        else:
            passed, evidence = _check_text(response_text, rule)
        if passed:
            passed_count += 1
        expectations.append({"text": rule["text"], "passed": passed, "evidence": evidence})

    return {
        "eval_id": eval_id,
        "expectations": expectations,
        "summary": {"passed": passed_count, "total": len(expectations)},
    }


def _load_eval_ids(evals_path: Path) -> set[int]:
    data = json.loads(evals_path.read_text(encoding="utf-8"))
    return {int(item["id"]) for item in data.get("evals", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade a single drawing-diagrams skill eval output")
    parser.add_argument("--evals", required=True, help="Path to evals.json")
    parser.add_argument("--eval-id", required=True, type=int, help="Eval id from evals.json")
    parser.add_argument("--output", required=True, help="Path to model reply markdown")
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

    if args.eval_id not in _load_eval_ids(evals_path):
        print(f"error: eval_id {args.eval_id} not present in {evals_path}", file=sys.stderr)
        return 1

    response_text = output_path.read_text(encoding="utf-8")
    svgs = collect_svgs(output_path, response_text)
    result = grade(args.eval_id, response_text, svgs)

    payload = json.dumps(result, indent=2)
    if args.write:
        Path(args.write).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
