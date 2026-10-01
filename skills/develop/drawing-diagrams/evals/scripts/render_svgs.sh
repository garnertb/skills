#!/bin/bash
#/ Usage: render_svgs.sh <iteration-dir>
#/
#/ Render every SVG under an iteration directory to a sibling PNG so the
#/ diagrams can be reviewed as images before automated grading runs. Output
#/ files land next to their source as <name>.png.
#/
#/ Finds a renderer in this order and uses the first available:
#/   rsvg-convert  (librsvg; `brew install librsvg`)
#/   cairosvg      (`pip install cairosvg`)
#/   qlmanage      (macOS Quick Look, preinstalled)
#/
#/ OPTIONS:
#/   -h | --help   Show this message.

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
if [ ! -d "$iteration_dir" ]; then
	echo "error: iteration directory not found: $iteration_dir" >&2
	exit 1
fi

render() {
	declare src="$1" dst="$2"
	if command -v rsvg-convert >/dev/null 2>&1; then
		rsvg-convert "$src" -o "$dst"
	elif command -v cairosvg >/dev/null 2>&1; then
		cairosvg "$src" -o "$dst"
	elif command -v qlmanage >/dev/null 2>&1; then
		# qlmanage writes <name>.svg.png into the output dir; normalize the name.
		qlmanage -t -s 1024 -o "$(dirname "$dst")" "$src" >/dev/null 2>&1
		mv "${src}.png" "$dst" 2>/dev/null || true
	else
		echo "error: no SVG renderer found (install librsvg or cairosvg)" >&2
		exit 1
	fi
}

count=0
# -print0 + read -d keeps paths with spaces intact.
while IFS= read -r -d '' svg; do
	png="${svg%.svg}.png"
	if render "$svg" "$png"; then
		echo "rendered: $png"
		count=$((count + 1))
	fi
done < <(find "$iteration_dir" -type f -name '*.svg' -print0)

echo "done: $count SVG(s) rendered"
