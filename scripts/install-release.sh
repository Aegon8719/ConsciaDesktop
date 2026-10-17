#!/usr/bin/env bash
set -euo pipefail
version=${CONSCIA_RELEASE_VERSION:?Release version is required}
action=${1:-install}
[[ $action == install || $action == update ]] || { echo 'Usage: installer [install|update]' >&2; exit 1; }
[[ $EUID != 0 ]] || { echo '请以有 sudo 权限的普通用户运行。' >&2; exit 1; }
source /etc/os-release
case "${ID:-}" in arch|endeavouros) ;; *) echo '仅支持 Arch / EndeavourOS。' >&2; exit 1 ;; esac
[[ $(uname -m) == x86_64 ]] || { echo '仅支持 x86_64。' >&2; exit 1; }
for tool in curl tar zstd sha256sum; do
    command -v "$tool" >/dev/null || { echo "缺少下载/解包工具：$tool" >&2; exit 1; }
done
name="ConsciaDesktop-$version-EndeavourOS-x86_64-offline"
url="https://github.com/Aegon8719/ConsciaDesktop/releases/download/v$version"
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/conscia-desktop/releases"
mkdir -p "$cache_root"
work=$(mktemp -d "$cache_root/$version.XXXXXX")
cd "$work"
curl --fail --location --retry 3 --output "$name.tar.zst" "$url/$name.tar.zst"
curl --fail --location --retry 3 --output "$name.tar.zst.sha256" "$url/$name.tar.zst.sha256"
sha256sum --check "$name.tar.zst.sha256"
tar --zstd --extract --no-same-owner --file "$name.tar.zst"
bash "$name/install-offline.sh" "$action"
echo "安装文件保留在 $work/$name"
