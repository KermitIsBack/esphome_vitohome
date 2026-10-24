#!/bin/zsh
set -e
cd -- "${0:A:h}"
bash scripts/setup_xiao.sh
.venv/bin/python -m pytest tests/unit -q
printf '\nEntwicklungsumgebung geprüft. Es wurde nichts geflasht.\n'
read '?Zum Schließen Enter drücken. '
