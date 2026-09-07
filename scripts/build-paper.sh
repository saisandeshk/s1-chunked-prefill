#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python3 "${project_root}/scripts/bootstrap-paper-tools.py"
mkdir -p "${project_root}/cache/tectonic" "${project_root}/paper/build"
XDG_CACHE_HOME="${project_root}/cache/tectonic" \
    "${project_root}/cache/tools/tectonic" \
    --keep-logs --keep-intermediates \
    --outdir "${project_root}/paper/build" "${project_root}/paper/main.tex"
