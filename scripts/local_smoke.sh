#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec "${GENX_PYTHON:-/usr/bin/python3}" "$SCRIPT_DIR/smoke.py" local "$@"
