#!/bin/bash
#/ Usage: grade_iteration.sh <iteration-dir>
#/
#/ Grade all Dependabot eval outputs inside an iteration directory.
#/ Looks for eval outputs at:
#/   <iteration-dir>/eval-<id>/<variant>/outputs/response.md
#/ Variants checked: with_skill, without_skill, old_skill
#/
#/ Writes grading JSON to:
#/   <iteration-dir>/eval-<id>/<variant>/grading.json
#/
#/ OPTIONS:
#/   -h | --help      Show this message.

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	grep '^#/' <"$0" | cut -c 4-
	exit 2
fi

set -o errexit -o nounset -o pipefail

if [ "$#" -ne 1 ]; then
	grep '^#/' <"$0" | cut -c 4-
	exit 2
fi

iteration_dir="$1"
evals_file="skills/dependabot/evals/evals.json"
script_file="skills/dependabot/evals/scripts/grade_eval.py"

if [ ! -d "${iteration_dir}" ]; then
	echo "error: iteration directory not found: ${iteration_dir}" >&2
	exit 1
fi
if [ ! -f "${evals_file}" ]; then
	echo "error: evals file not found: ${evals_file}" >&2
	exit 1
fi
if [ ! -f "${script_file}" ]; then
	echo "error: grader script not found: ${script_file}" >&2
	exit 1
fi

jq -r '.evals[].id' "${evals_file}" | while read -r eval_id; do
	for variant in with_skill without_skill old_skill; do
		output_file="${iteration_dir}/eval-${eval_id}/${variant}/outputs/response.md"
		grading_file="${iteration_dir}/eval-${eval_id}/${variant}/grading.json"
		if [ -f "${output_file}" ]; then
			python3 "${script_file}" \
				--evals "${evals_file}" \
				--eval-id "${eval_id}" \
				--output "${output_file}" \
				--write "${grading_file}"
			echo "graded: ${grading_file}"
		fi
	done
done
