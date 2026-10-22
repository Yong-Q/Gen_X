#!/usr/bin/env bash
set -euo pipefail
# Absolute paths are supplied as separate sbatch arguments, including spaces.
# Standard-library /usr/bin/python3 avoids login-node Conda/glibc assumptions.
unset PYTHONHOME PYTHONPATH LD_LIBRARY_PATH
exec "$1" "$2" worker --run-dir "$3"
