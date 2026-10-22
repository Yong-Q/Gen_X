#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
out_arg=${1:-"reports/$(date -u +%Y%m%dT%H%M%SZ)"}
if [[ "$out_arg" = /* ]]; then
  printf 'Use an output path inside the repository.\n' >&2
  exit 2
fi
case "/$out_arg/" in *"/../"*) printf 'Parent traversal is not allowed.\n' >&2; exit 2;; esac
out_dir=$(python3 - "$repo_root" "$out_arg" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
destination = (root / sys.argv[2]).resolve()
if destination == root or root not in destination.parents:
    raise SystemExit('Output directory must resolve inside the repository')
try:
    destination.mkdir(parents=True, exist_ok=False)
except FileExistsError:
    raise SystemExit('Refusing to reuse an existing snapshot directory: ' + str(destination))
print(destination)
PY
)
for cmd in pandoc xelatex fc-match; do command -v "$cmd" >/dev/null; done
cjk_regular=${GENX_CJK_REGULAR:-$(fc-match -f '%{file}' 'Noto Sans CJK SC')}
cjk_bold=${GENX_CJK_BOLD:-$(fc-match -f '%{file}' 'Noto Sans CJK SC:style=Bold')}
[[ -f "$cjk_regular" && -f "$cjk_bold" ]]
cjk_dir=$(dirname -- "$cjk_regular")
cjk_file=$(basename -- "$cjk_regular")
cjk_bold_file=$(basename -- "$cjk_bold")
common=(--from=markdown --pdf-engine=xelatex --standalone --toc
  --lua-filter="$repo_root/tools/pdf_links.lua" --include-in-header="$repo_root/tools/pdf_style.tex"
  -V 'documentclass=article' -V 'mainfont=DejaVu Sans' -V "CJKmainfont=$cjk_file"
  -V "CJKoptions=Path=$cjk_dir/,BoldFont=$cjk_bold_file,Scale=1"
  -V 'geometry:margin=20mm' -V 'fontsize=10pt' -V 'colorlinks=true' -V 'urlcolor=blue'
  -V 'linestretch=1.12' -V 'papersize=a4' -M 'date=2026-10-22')
pandoc "$repo_root/docs/literature_survey.md" "$repo_root/docs/potentials_and_environment.md" \
  "${common[@]}" -M 'title=构型概率分布的学习与生成：文献调研' \
  -o "$out_dir/literature_survey.pdf" >"$out_dir/literature_build.log" 2>&1
pandoc "$repo_root/docs/technical_roadmap.md" "$repo_root/docs/smoke_results.md" \
  "${common[@]}" -M 'title=Gen_X：可行技术路线与运行记录' \
  -o "$out_dir/technical_roadmap.pdf" >"$out_dir/roadmap_build.log" 2>&1
if [[ -f "$repo_root/docs/real_generation_results.md" ]]; then
  pandoc "$repo_root/docs/real_generation_results.md" "${common[@]}" \
    -M 'title=bgmat单珠水冰：真实生成示例与复跑教程' \
    -o "$out_dir/bgmat_cpu_generation.pdf" >"$out_dir/generation_build.log" 2>&1
fi
printf '%s\n' "$out_dir/literature_survey.pdf" "$out_dir/technical_roadmap.pdf"
