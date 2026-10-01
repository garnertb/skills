---
name: drawing-diagrams
description: >
  Turn systems, processes, and flows into clear, hand-drawn whiteboard-style SVG
  diagrams — flowcharts, architecture diagrams, sequence flows, and system maps.
  Use when asked to "draw a diagram", "make a flowchart", "visualize this
  architecture", "sketch the flow", "diagram the system", or produce an
  "excalidraw-style" diagram.
metadata:
  author: garnertb
  version: "1.1"
---

# Drawing Diagrams

Turn systems, processes, and flows into clear technical diagrams delivered as
smooth, clean, whiteboard-style SVG. The diagram is the deliverable — keep prose
minimal.

See [references/svg-style.md](references/svg-style.md) for the annotated SVG
skeleton, reusable snippets (markers, swimlanes, numbered badges), and a
complete worked example.

## Constraints

- ONLY produce diagrams plus the minimal explanation needed to use them.
- NEVER write application code, refactor, or run builds/tests.
- NEVER use gradients, drop shadows, 3D effects, or polished corporate styling.
- NEVER default to raster output — produce SVG with a transparent background.
- Do NOT overcrowd the canvas. When in doubt, add whitespace and split into
  multiple diagrams.

## Visual style (non-negotiable)

- Clean, spacious layout with ample whitespace; readable at a glance.
- Nodes are rounded rectangles (`rx`) with subtle tinted fills and solid
  outlines.
- Monospace font for every label:
  `ui-monospace, 'JetBrains Mono', Menlo, monospace`.
- Connect elements with orthogonal (90°) lines only — horizontal/vertical
  segments, no diagonals or curves for connectors.
- Number key steps (1, 2, 3…) whenever sequence matters.
- Use swimlanes (labeled bands) when they clarify responsibilities or system
  boundaries.
- Add a compact legend only when colors or symbols need explanation.
- Keep a limited, tasteful palette (2–4 tints) for consistency.
- Keep strokes smooth and clean — crisp outlines, even line weights, no wobble.

## Workflow

Copy this checklist into your response and check items off as you go:

- [ ] **Clarify the subject.** Identify the actors/components, the steps, and
      whether sequence or ownership (swimlanes) matters. Ask only if genuinely
      ambiguous.
- [ ] **Plan the layout.** Choose orientation, lanes, and step order. Reserve
      generous spacing so nothing crowds.
- [ ] **Author the SVG** by hand using the snippets in
      [references/svg-style.md](references/svg-style.md): transparent
      background, rounded-rect nodes, orthogonal connectors with `<marker>`
      arrowheads, monospace labels, numbered badges, swimlanes, and a legend
      when needed.
- [ ] **Validate.** Confirm the file is well-formed XML, the background is
      transparent (no full-canvas `<rect>` fill), connectors are orthogonal, and
      nothing overlaps. Fix and repeat until all pass.
- [ ] **Save** to a sensible path (default: `./diagrams/<slug>.svg`).

## Output format

Reply with:

1. The saved file path.
2. A one-line description of what the diagram shows.
3. A short legend/key if colors or symbols were used.

Keep everything else terse — the diagram speaks for itself.
