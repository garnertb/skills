# Drawing-diagrams evals

Eval prompts and grading for the `drawing-diagrams` skill. Because the output is
SVG, grading has two layers: a **human visual-review pass** on rendered images,
then **deterministic checks** on the SVG structure and reply text.

## Contents

- `evals.json`: prompts covering basic generation, sequence flows, swimlanes,
  the no-decoration constraint, overcrowding, and scope boundaries.
- `scripts/render_svgs.sh`: renders every SVG in an iteration to PNG for review.
- `scripts/grade_eval.py`: grades one output file for a single eval ID.
- `scripts/grade_iteration.sh`: grades every output in an iteration directory.
- `fixtures/`: reference "good" SVGs per eval (e.g. `eval-1-good.svg`).

## What the automated grader can and cannot judge

The structural checks catch the objective, non-negotiable rules: well-formed
XML, a transparent background, no gradients/shadows/3D, vector (not raster)
output, orthogonal connectors, numbered badges, and swimlane bands.

They **cannot** judge whether a diagram actually reads well — crossing
connectors, colliding labels, cramped spacing, or a confusing layout all pass
the parser. That is what the visual-review step is for.

## Workflow

1. Generate model outputs for each prompt in `evals.json`. Save the reply and
   the generated SVG(s) to:

   ```text
   <workspace>/iteration-<N>/eval-<id>/<variant>/outputs/response.md
   <workspace>/iteration-<N>/eval-<id>/<variant>/outputs/<slug>.svg
   ```

   `<variant>` is `with_skill`, `without_skill`, or `old_skill`. SVGs can be
   separate files (preferred) or embedded in `response.md`; the grader reads
   both.

2. **Render for visual review** — turn every SVG into a PNG, then look at them
   and record feedback before grading:

   ```bash
   bash skills/develop/drawing-diagrams/evals/scripts/render_svgs.sh <workspace>/iteration-1
   ```

   Review the images and note anything the parser can't see — awkward spacing,
   crossed connectors, unclear labels. Feed that feedback into the next skill
   iteration; it is the primary signal for a visual skill.

3. **Run the deterministic checks:**

   ```bash
   bash skills/develop/drawing-diagrams/evals/scripts/grade_iteration.sh <workspace>/iteration-1
   ```

4. Optional — grade a single output and print JSON to stdout:

   ```bash
   python3 skills/develop/drawing-diagrams/evals/scripts/grade_eval.py \
     --evals skills/develop/drawing-diagrams/evals/evals.json \
     --eval-id 1 \
     --output <workspace>/iteration-1/eval-1/with_skill/outputs/response.md
   ```

## Requirements

- Python 3.9+ (grader uses only the standard library).
- `jq` for `grade_iteration.sh`.
- An SVG renderer for `render_svgs.sh`: `librsvg` (`brew install librsvg`),
  `cairosvg` (`pip install cairosvg`), or macOS Quick Look (`qlmanage`,
  preinstalled). The script falls back through them in that order.
