# SVG Style Reference

Techniques and reusable snippets for authoring smooth, clean, whiteboard-style
SVG diagrams. Author SVG by hand — do not reach for a rendering library.

## Contents

- [Canvas and palette](#canvas-and-palette)
- [Arrowhead markers](#arrowhead-markers)
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

A three-step request flow across two swimlanes, with numbered badges, orthogonal
connectors, and a transparent background. Use it as a starting skeleton.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 320">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#3f3f46" />
    </marker>
  </defs>
  <style>
    text { font-family: ui-monospace, 'JetBrains Mono', Menlo, monospace; }
  </style>

  <!-- swimlanes -->
  <rect x="20" y="24" width="600" height="120" rx="6"
        fill="#f4f4f5" stroke="#d4d4d8" stroke-width="1.5" />
  <text x="36" y="48" font-size="13" fill="#52525b">Client</text>
  <rect x="20" y="168" width="600" height="120" rx="6"
        fill="#f4f4f5" stroke="#d4d4d8" stroke-width="1.5" />
  <text x="36" y="192" font-size="13" fill="#52525b">Server</text>

  <!-- nodes -->
  <rect x="70" y="66" width="160" height="56" rx="10"
        fill="#eff6ff" stroke="#1d4ed8" stroke-width="2" />
  <text x="150" y="99" text-anchor="middle" font-size="14" fill="#1e3a8a">Browser</text>

  <rect x="400" y="66" width="160" height="56" rx="10"
        fill="#eff6ff" stroke="#1d4ed8" stroke-width="2" />
  <text x="480" y="99" text-anchor="middle" font-size="14" fill="#1e3a8a">API</text>

  <rect x="400" y="210" width="160" height="56" rx="10"
        fill="#ecfdf5" stroke="#047857" stroke-width="2" />
  <text x="480" y="243" text-anchor="middle" font-size="14" fill="#065f46">Database</text>

  <!-- 1: browser -> api -->
  <path d="M230,94 L400,94" fill="none" stroke="#3f3f46" stroke-width="2"
        stroke-linecap="round" marker-end="url(#arrow)" />
  <circle cx="315" cy="94" r="11" fill="#1d4ed8" />
  <text x="315" y="99" text-anchor="middle" font-size="13" fill="#ffffff">1</text>

  <!-- 2: api -> database -->
  <path d="M480,122 L480,210" fill="none" stroke="#3f3f46" stroke-width="2"
        stroke-linecap="round" marker-end="url(#arrow)" />
  <circle cx="480" cy="166" r="11" fill="#047857" />
  <text x="480" y="171" text-anchor="middle" font-size="13" fill="#ffffff">2</text>

  <!-- 3: database -> api (response) -->
  <path d="M400,238 L300,238 L300,110 L230,110" fill="none" stroke="#3f3f46"
        stroke-width="2" stroke-linecap="round" marker-end="url(#arrow)" />
  <circle cx="300" cy="174" r="11" fill="#c2410c" />
  <text x="300" y="179" text-anchor="middle" font-size="13" fill="#ffffff">3</text>
</svg>
```
