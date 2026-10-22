#!/usr/bin/env bash
# Render editable, proposed-research methodology diagrams; never runs models/jobs.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
figure_dir="$project_dir/docs/figures/research_v2"
command -v dot >/dev/null
for source in "$figure_dir"/*.dot; do
  for format in svg pdf; do
    target="${source%.dot}.$format"
    if [[ -e "$target" ]]; then
      printf 'Refusing to overwrite existing result: %s\n' "$target" >&2
      exit 1
    fi
  done
done
for source in "$figure_dir"/*.dot; do
  for format in svg pdf; do
    target="${source%.dot}.$format"
    dot -T"$format" "$source" -o "$target"
    printf '%s\n' "$target"
  done
done
