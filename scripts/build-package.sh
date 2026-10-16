#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID != 0 ]] || { echo 'makepkg 必须以普通用户运行。' >&2; exit 1; }
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/conscia-desktop"
mkdir -p "$cache_root"
work=${1:-$(mktemp -d "$cache_root/build.XXXXXX")}
destination=${2:-$root/dist}
mkdir -p "$work" "$destination"
python3 - "$work" "$destination" <<'PY'
from pathlib import Path
import shlex
import sys
work, output = map(Path, sys.argv[1:])
(work / 'makepkg.conf').write_text('source /etc/makepkg.conf\n' +
    'BUILDDIR=' + shlex.quote(str(work / 'build')) + '\n' +
    'PKGDEST=' + shlex.quote(str(output)) + '\n')
PY
cd "$root/packages/arch"
makepkg --config "$work/makepkg.conf" --syncdeps --noconfirm --nocheck
echo "软件包已输出到 $destination；临时源码位于 $work"
