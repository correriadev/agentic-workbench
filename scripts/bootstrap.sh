#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.12+ from python.org or your OS package manager; then retry.' >&2
  exit 1
fi
python3 -c 'import sys; raise SystemExit(sys.version_info < (3,12))'
exec python3 "$ROOT/scripts/environment.py" "$@"
