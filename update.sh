#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ $# == 0 ]]; then
    export ConsciaDesktopReleaseVersion=$(sed -n 's/.*"version": "\([^"]*\)".*/\1/p' "$root/versions.lock")
    exec bash "$root/scripts/install-release.sh" update
fi
if [[ ${1:-} == --build ]]; then shift; fi
source "$root/scripts/bootstrap.sh"
exec python3 "$root/scripts/manage.py" update "$@"
