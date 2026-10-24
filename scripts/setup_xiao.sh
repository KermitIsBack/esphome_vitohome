#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  if [[ -n "${VITODENS_PYTHON:-}" ]]; then
    python_bin="$VITODENS_PYTHON"
  elif command -v python3.12 >/dev/null 2>&1; then
    python_bin="$(command -v python3.12)"
  else
    printf 'Python 3.12 benötigt. Alternativ VITODENS_PYTHON=/Pfad/python3 setzen.\n' >&2
    exit 1
  fi
  "$python_bin" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-dev.txt
bash scripts/check_xiao.sh
