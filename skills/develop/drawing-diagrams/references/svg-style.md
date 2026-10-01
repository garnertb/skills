# SVG Style Reference

Techniques and reusable snippets for authoring smooth, clean, whiteboard-style
SVG diagrams. Author SVG by hand — do not reach for a rendering library.

## Contents

- [Canvas and palette](#canvas-and-palette)
- [Arrowhead markers](#arrowhead-markers)
- [Timeline layout (default)](#timeline-layout-default)
- [Nodes](#nodes)
- [Orthogonal connectors](#orthogonal-connectors)
- [Numbered step badges](#numbered-step-badges)
- [Swimlanes](#swimlanes)
- [Legend](#legend)
- [Complete worked example](#complete-worked-example)

## Canvas and palette

- Open with `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H">`.
- NEVER add a full-canvas `<rect>` fill — the background stays transparent.
- Define the font once in a `<style>` block and inherit it on `<text>`.
- Pick 2–4 tints and reuse them. A calm default set:

| Role     | Fill      | Stroke    |
| -------- | --------- | --------- |
| Neutral  | `#f4f4f5` | `#3f3f46` |
| Accent A | `#eff6ff` | `#1d4ed8` |
| Accent B | `#ecfdf5` | `#047857` |
| Warning  | `#fff7ed` | `#c2410c` |

```xml
<style>
  text { font-family: ui-monospace, 'JetBrains Mono', Menlo, monospace; }
</style>
```

## Arrowhead markers

Define one marker and reuse it on every connector via `marker-end`.

```xml
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="#3f3f46" />
  </marker>
</defs>
```

## Timeline layout (default)

For any sequence, flow, or process, lay the diagram out as a **horizontal,
left-to-right timeline**: time advances along the x-axis, steps sit in order
from left to right, and a baseline time axis makes the direction explicit. Stack
swimlanes as horizontal bands beneath the timeline when actors or tiers matter;
drop a step down into the relevant lane and bring it back to the axis.

- Place event nodes along a shared top row at evenly spaced x positions.
- Draw a single horizontal time axis near the bottom with one arrowhead on the
  right so the direction of time is unmistakable.
- Number the steps left to right; keep every connector orthogonal.

```xml
<!-- event nodes, left to right -->
<rect x="60"  y="60" width="150" height="54" rx="10" fill="#eff6ff" stroke="#1d4ed8" stroke-width="2"/>
<rect x="300" y="60" width="150" height="54" rx="10" fill="#eff6ff" stroke="#1d4ed8" stroke-width="2"/>
<rect x="540" y="60" width="150" height="54" rx="10" fill="#eff6ff" stroke="#1d4ed8" stroke-width="2"/>

<!-- time axis: one long horizontal arrow, left to right -->
<path d="M40,170 L720,170" fill="none" stroke="#a1a1aa" stroke-width="2"
      stroke-linecap="round" marker-end="url(#arrow)" />
<text x="700" y="190" text-anchor="end" font-size="12" fill="#71717a">time →</text>
```

## Nodes

Rounded rectangle plus a centered label. Keep padding generous.

```xml
<g>
  <rect x="60" y="60" width="180" height="64" rx="10"
        fill="#eff6ff" stroke="#1d4ed8" stroke-width="2" />
  <text x="150" y="97" text-anchor="middle" font-size="15" fill="#1e3a8a">
    API Gateway
  </text>
</g>
```

## Orthogonal connectors

Connectors move in horizontal/vertical segments only — no diagonals or curves.
Route them with an L-shaped or Z-shaped `path`.

```xml
<!-- down then right: -->
<path d="M150,124 L150,170 L300,170" fill="none"
      stroke="#3f3f46" stroke-width="2" stroke-linecap="round"
      marker-end="url(#arrow)" />
```

## Numbered step badges

When sequence matters, tag each connector or node with a small numbered circle.

```xml
<g>
  <circle cx="150" cy="147" r="11" fill="#1d4ed8" />
  <text x="150" y="152" text-anchor="middle" font-size="13" fill="#ffffff">1</text>
</g>
```

## Swimlanes

Labeled bands that group nodes by actor or system boundary. Draw them first, as
a background layer, so nodes sit on top.

```xml
<g>
  <rect x="20" y="40" width="760" height="120" rx="6"
        fill="#f4f4f5" stroke="#d4d4d8" stroke-width="1.5" />
  <text x="36" y="64" font-size="13" fill="#52525b">Client</text>
</g>
```

## Legend

Include only when colors or symbols need explanation. A small stack of swatch +
label rows in a corner.

```xml
<g transform="translate(600,320)">
  <rect x="0" y="0" width="14" height="14" rx="3" fill="#eff6ff" stroke="#1d4ed8"/>
  <text x="22" y="12" font-size="12" fill="#3f3f46">Service</text>
</g>
```

## Complete worked example

A horizontal left-to-right timeline (the default layout): three sequenced steps
along a shared row, a bottom time axis, swimlanes stacked beneath, numbered
badges, orthogonal connectors, and a transparent background. Use it as a
starting skeleton.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 300">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#3f3f46" />
    </marker>
  </defs>
  <style>
    text { font-family: ui-monospace, 'JetBrains Mono', Menlo, monospace; }
  </style>

  <!-- swimlanes stacked under the timeline -->
  <rect x="20" y="40" width="720" height="92" rx="6"
        fill="#f4f4f5" stroke="#d4d4d8" stroke-width="1.5" />
  <text x="36" y="62" font-size="13" fill="#52525b">Client</text>
  <rect x="20" y="148" width="720" height="92" rx="6"
        fill="#f4f4f5" stroke="#d4d4d8" stroke-width="1.5" />
  <text x="36" y="170" font-size="13" fill="#52525b">Server</text>

  <!-- event nodes, left to right in time order -->
  <rect x="70" y="70" width="170" height="54" rx="10"
        fill="#eff6ff" stroke="#1d4ed8" stroke-width="2" />
  <text x="155" y="102" text-anchor="middle" font-size="14" fill="#1e3a8a">Request</text>

  <rect x="300" y="178" width="170" height="54" rx="10"
        fill="#eff6ff" stroke="#1d4ed8" stroke-width="2" />
  <text x="385" y="210" text-anchor="middle" font-size="14" fill="#1e3a8a">Validate</text>

  <rect x="530" y="70" width="170" height="54" rx="10"
        fill="#ecfdf5" stroke="#047857" stroke-width="2" />
  <text x="615" y="102" text-anchor="middle" font-size="14" fill="#065f46">Respond</text>

  <!-- 1: request -> validate -->
  <path d="M240,97 L385,97 L385,178" fill="none" stroke="#3f3f46" stroke-width="2"
        stroke-linecap="round" marker-end="url(#arrow)" />
  <circle cx="385" cy="150" r="11" fill="#1d4ed8" />
  <text x="385" y="155" text-anchor="middle" font-size="13" fill="#ffffff">1</text>

  <!-- 2: validate -> respond -->
  <path d="M470,205 L615,205 L615,124" fill="none" stroke="#3f3f46" stroke-width="2"
        stroke-linecap="round" marker-end="url(#arrow)" />
  <circle cx="615" cy="150" r="11" fill="#047857" />
  <text x="615" y="155" text-anchor="middle" font-size="13" fill="#ffffff">2</text>

  <!-- time axis -->
  <path d="M40,268 L720,268" fill="none" stroke="#a1a1aa" stroke-width="2"
        stroke-linecap="round" marker-end="url(#arrow)" />
  <text x="720" y="288" text-anchor="end" font-size="12" fill="#71717a">time →</text>
</svg>
```
