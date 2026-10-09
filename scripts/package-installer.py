#!/usr/bin/env python3
"""Create a small self-extracting installer containing this repository only."""
import os
from pathlib import Path
import shutil
import tarfile
import tempfile

root = Path(__file__).resolve().parent.parent
output = root / "dist/ConsciaDesktop-EndeavourOS.run"
output.parent.mkdir(parents=True, exist_ok=True)
launcher = r'''#!/usr/bin/env bash
set -euo pipefail
[[ $EUID != 0 ]] || { echo '请以普通用户运行，不要给整条命令加 sudo。' >&2; exit 1; }
source /etc/os-release
case "${ID:-}" in arch|endeavouros) ;; *) echo '目前支持 EndeavourOS / Arch Linux。' >&2; exit 1 ;; esac
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/conscia-desktop"
mkdir -p "$cache_root"
work=$(mktemp -d "$cache_root/installer.XXXXXX")
trap 'echo "安装中断，可在 $work/ConsciaDesktop 中重试；中断事务使用 rollback.sh --recover。" >&2' ERR
line=$(awk '/^__CONSCIA_PAYLOAD__$/ { print NR + 1; exit }' "$0")
tail -n +"$line" "$0" | tar -xz --no-same-owner -C "$work"
bash "$work/ConsciaDesktop/install.sh" "$@"
echo "维护脚本保留在：$work/ConsciaDesktop；可使用正式 Git checkout 替代。"
exit 0
__CONSCIA_PAYLOAD__
'''
with tempfile.TemporaryDirectory(prefix="conscia-installer-") as temporary:
    payload = Path(temporary) / "payload.tar.gz"
    def include(info):
        if any(part in (".git", "__pycache__", "dist") for part in Path(info.name).parts):
            return None
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        return info
    with tarfile.open(payload, "w:gz") as archive:
        for name in ("install.sh", "update.sh", "rollback.sh", "uninstall.sh", "versions.lock",
                     "config", "scripts", "packages", "README.md"):
            archive.add(root / name, arcname="ConsciaDesktop/" + name, filter=include)
    target = output.with_suffix(".tmp")
    with target.open("wb") as result:
        result.write(launcher.encode())
        with payload.open("rb") as source:
            shutil.copyfileobj(source, result)
    target.chmod(0o755)
    os.replace(target, output)
    print(f"Created {output} ({output.stat().st_size / 1024 / 1024:.1f} MiB)")
