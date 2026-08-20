# Dependabot evals

This directory contains eval prompts and grading scripts for the full Dependabot
skill.

## Contents

- `evals.json`: test prompts that cover no-arg routing, report, plan, config,
  and general Dependabot behavior.
- `scripts/grade_eval.py`: grades one output file for a single eval ID.
- `scripts/grade_iteration.sh`: grades all outputs in an iteration directory.

## Quick start

1. Generate model outputs for each prompt in `evals.json`.
2. Save each output to:

```text
<workspace>/iteration-<N>/eval-<id>/<variant>/outputs/response.md
```

`<variant>` can be `with_skill`, `without_skill`, or `old_skill`.

3. Grade all found outputs:

```bash
bash skills/dependabot/evals/scripts/grade_iteration.sh <workspace>/iteration-1
```

4. Optional: grade a single output and print JSON to stdout:

```bash
python3 skills/dependabot/evals/scripts/grade_eval.py \
  --evals skills/dependabot/evals/evals.json \
  --eval-id 2 \
  --output <workspace>/iteration-1/eval-2/with_skill/outputs/response.md
```

## Benchmark viewer workflow

After collecting `grading.json` files, create benchmark artifacts and run the
reviewer:

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-1 --skill-name dependabot
python <skill-creator-path>/eval-viewer/generate_review.py <workspace>/iteration-1 --skill-name dependabot --benchmark <workspace>/iteration-1/benchmark.json
```
