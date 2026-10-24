#!/usr/bin/env bash
# Compile only. Dummy credentials remain in ignored .validation/, never devices/.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
bash scripts/check_xiao.sh
export PLATFORMIO_CORE_DIR="$PWD/.platformio"
exec .venv/bin/esphome compile .validation/xiao/read-only.yaml
