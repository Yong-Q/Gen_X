#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$repo_root"
unset PYTHONHOME PYTHONPATH
python310=${GENX_PYTHON310:-python3}
"$python310" -c 'import sys; assert sys.version_info[:2] == (3,10), "Set GENX_PYTHON310 to Python 3.10"'
revision=6e3db2b3453cb57eb16fdd2148c95ec35264faf4
mkdir -p external .cache/tmp .cache/pip .cache/uv
if [[ ! -d external/bgmat ]]; then
  git clone https://github.com/maxschebek/bgmat.git external/bgmat
  git -C external/bgmat checkout --detach "$revision"
fi
[[ "$(git -C external/bgmat rev-parse HEAD)" == "$revision" ]]
if [[ ! -d .venv-bgmat ]]; then "$python310" -m venv .venv-bgmat; fi
export TMPDIR="$repo_root/.cache/tmp"
export PIP_CACHE_DIR="$repo_root/.cache/pip"
export UV_CACHE_DIR="$repo_root/.cache/uv"
if command -v uv >/dev/null 2>&1; then
  uv pip install --python .venv-bgmat/bin/python -r configs/bgmat_requirements.lock.txt
  uv pip install --python .venv-bgmat/bin/python --no-deps -e external/bgmat
else
  .venv-bgmat/bin/python -m pip install -r configs/bgmat_requirements.lock.txt
  .venv-bgmat/bin/python -m pip install --no-deps -e external/bgmat
fi
.venv-bgmat/bin/python - <<'PY'
from pathlib import Path
import hashlib,json
root=Path('external/bgmat')
lock=json.loads(Path('configs/bgmat_source_lock.json').read_text())
for name,expected in lock['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected, name
weight=root/'tutorial/params_trained/params-mw_cubic_216.pkl'
assert hashlib.sha256(weight.read_bytes()).hexdigest()=='89d03c7ae3980421f313b0495b89d92a9f107804f4d936fcd99b34dd4cb294ba'
print('Pinned source, checkpoint, and Python environment are ready. Inference still requires Slurm.')
PY
