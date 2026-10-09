#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$root/scripts/bootstrap.sh"
exec python3 "$root/scripts/manage.py" install "$@"
