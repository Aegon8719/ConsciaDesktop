#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
[[ $EUID != 0 ]] || { echo '请以普通用户在 Arch 构建环境中运行。' >&2; exit 1; }
[[ -e /etc/arch-release && $(uname -m) == x86_64 ]] || { echo '需要 Arch x86_64 构建环境。' >&2; exit 1; }
work=${1:-$(mktemp -d "${TMPDIR:-/tmp}/conscia-offline.XXXXXX")}
mkdir -p "$work" "$root/dist"
work=$(cd "$work" && pwd)
version=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$root/versions.lock")
name="ConsciaDesktop-$version-EndeavourOS-x86_64-offline"
bundle="$work/$name"
mkdir -p "$bundle"/{repo,desktop,greeter}
if ! compgen -G "$bundle/desktop/conscia-desktop-*.pkg.tar.zst" >/dev/null; then
    bash "$root/scripts/build-package.sh" "$work/build" "$bundle/desktop"
fi

if ! compgen -G "$bundle/greeter/*.pkg.tar.zst" >/dev/null; then
    if [[ ! -d "$work/greeter/.git" ]]; then
        git clone --depth=1 https://aur.archlinux.org/greetd-dms-greeter-bin.git "$work/greeter"
    fi
    (cd "$work/greeter" && PKGDEST="$bundle/greeter" makepkg --syncdeps --noconfirm --nocheck)
fi

# Resolve against an empty installed-package database, so builder dependencies
# cannot accidentally disappear from the offline bundle.
python3 - "$bundle" <<'PY'
from pathlib import Path
import subprocess
import sys
bundle = Path(sys.argv[1])
targets = {"base", "sudo", "archlinux-keyring", "greetd", "python"}
for directory in ("desktop", "greeter"):
    for package in (bundle / directory).glob("*.pkg.tar.zst"):
        info = subprocess.check_output(["bsdtar", "-xOf", str(package), ".PKGINFO"], text=True)
        targets.update(line.removeprefix("depend = ") for line in info.splitlines() if line.startswith("depend = "))
(bundle / "targets.txt").write_text("\n".join(sorted(targets)) + "\n")
PY
mapfile -t targets < "$bundle/targets.txt"
mkdir -p "$work/db/local"
cp -a /var/lib/pacman/sync "$work/db/"
python3 - "$work/db" "$bundle/repo" "${targets[@]}" <<'PY'
import base64
from pathlib import Path
import shutil
import subprocess
import sys
database, repository = map(Path, sys.argv[1:3])
records = subprocess.check_output([
    "pacman", "--dbpath", str(database), "-Sp", "--noconfirm",
    "--print-format", "%f %g", *sys.argv[3:]], text=True)
for record in records.splitlines():
    filename, signature = record.split(" ", 1)
    cached = Path("/var/cache/pacman/pkg") / filename
    if cached.is_file() and not (repository / filename).exists():
        shutil.copy2(cached, repository / filename)
    (repository / (filename + ".sig")).write_bytes(base64.b64decode(signature, validate=True))
PY
sudo pacman --dbpath "$work/db" --cachedir "$bundle/repo" --logfile "$work/download.log" \
    -Sw --noconfirm "${targets[@]}"
sudo chown -R "$(id -u):$(id -g)" "$bundle/repo"
repo-add "$bundle/repo/conscia-offline.db.tar.gz" "$bundle"/repo/*.pkg.tar.zst
for entry in scripts config packages versions.lock README.md install.sh update.sh rollback.sh uninstall.sh; do
    cp -a "$root/$entry" "$bundle/"
done
cat > "$bundle/install-offline.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec bash "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/scripts/install-offline.sh" "$@"
EOF
chmod +x "$bundle/install-offline.sh"
date -u +'%Y-%m-%dT%H:%M:%SZ' > "$bundle/built-at.txt"
pacman -Qp "$bundle"/repo/*.pkg.tar.zst "$bundle"/desktop/*.pkg.tar.zst "$bundle"/greeter/*.pkg.tar.zst > "$bundle/packages.txt"
(cd "$bundle" && find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS)
tar -C "$work" -I 'zstd -T2 -3' -cf "$root/dist/$name.tar.zst" "$name"
(cd "$root/dist" && sha256sum "$name.tar.zst" > "$name.tar.zst.sha256")
python3 "$root/scripts/package-installer.py"
echo "Created $root/dist/$name.tar.zst"
