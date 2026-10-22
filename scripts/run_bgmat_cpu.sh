#!/usr/bin/env bash
set -euo pipefail
: "${SLURM_JOB_ID:?Submit through Slurm}"
# sbatch executes a copy under /var/spool, so BASH_SOURCE is not the repo path.
repo_root=$(cd -- "${SLURM_SUBMIT_DIR:?Submit from the repository root}" && pwd)
[[ -f "$repo_root/scripts/bgmat_inference.py" ]]
export JAX_PLATFORMS=cpu
export JAX_ENABLE_X64=true
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"
export OPENBLAS_NUM_THREADS="$OMP_NUM_THREADS"
export MKL_NUM_THREADS="$OMP_NUM_THREADS"
export TF_NUM_INTEROP_THREADS=1
export TF_NUM_INTRAOP_THREADS="$OMP_NUM_THREADS"
export MPLCONFIGDIR="$repo_root/.cache/matplotlib"
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONHOME PYTHONPATH LD_LIBRARY_PATH
exec srun --export=ALL --cpu-bind=cores "$repo_root/.venv-bgmat/bin/python" \
  "$repo_root/scripts/bgmat_inference.py" "$@"
