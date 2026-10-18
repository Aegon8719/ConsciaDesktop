#!/usr/bin/env bash
set -euo pipefail
bundle=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
action=${1:-install}
[[ $action == install || $action == update ]] || { echo 'Usage: install-offline.sh [install|update]' >&2; exit 1; }
[[ $EUID != 0 ]] || { echo '请以有 sudo 权限的普通用户运行。' >&2; exit 1; }
source /etc/os-release
case "${ID:-}" in arch|endeavouros) ;; *) echo '仅支持 Arch / EndeavourOS。' >&2; exit 1 ;; esac
[[ $(uname -m) == x86_64 ]] || { echo '仅支持 x86_64。' >&2; exit 1; }
cd "$bundle"
sha256sum --check --quiet SHA256SUMS
# Refuse before changing packages; old snapshots require the old installer.
legacy_state="${XDG_STATE_HOME:-$HOME/.local/state}/conscia-desktop"
if [[ -e /var/lib/conscia-desktop/owner || -e "$legacy_state/installation.json" || -e "$legacy_state/pending.json" ]] || pacman -Q conscia-desktop &>/dev/null; then
    echo '检测到旧命名版本。请先使用旧版安装目录执行 bash uninstall.sh；有中断事务时先执行 bash rollback.sh --recover，再安装 ConsciaDesktop。' >&2
    exit 1
fi
if [[ $action == install ]] && { [[ -e /var/lib/ConsciaDesktop/owner ]] || pacman -Q ConsciaDesktop &>/dev/null; }; then
    echo 'Conscia 已安装，请使用原有更新流程。' >&2
    exit 1
fi
if [[ $action == update ]] && ! pacman -Q ConsciaDesktop &>/dev/null; then
    echo 'Conscia 尚未安装。' >&2
    exit 1
fi
if [[ -r /var/lib/ConsciaDesktop/owner ]] && [[ $(cat /var/lib/ConsciaDesktop/owner) != "$(id -u)" ]]; then
    echo '请由原安装用户更新 Conscia。' >&2
    exit 1
fi
if systemctl --user is-active --quiet niri.service dms.service; then
    echo '请注销桌面，在本机 TTY 中安装或更新。' >&2
    exit 1
fi
sudo -v
# Pacman's download user must be able to read packages even from a private USB mount.
stage=$(sudo mktemp -d /var/cache/ConsciaDesktopOffline.XXXXXX)
trap 'sudo rm -rf -- "$stage"' EXIT
sudo chmod 755 "$stage"
sudo cp -a repo "$stage/repo"
sudo chmod -R a+rX "$stage/repo"
config=$(mktemp)
trap 'rm -f -- "$config"; sudo rm -rf -- "$stage"' EXIT
cat > "$config" <<EOF
[options]
Architecture = x86_64
SigLevel = Required DatabaseOptional
LocalFileSigLevel = Optional
CacheDir = $stage/repo
[ConsciaDesktopOffline]
Server = file://$stage/repo
EOF
mapfile -t targets < targets.txt
# This configuration has no network repositories or mirrorlists.
sudo pacman --config "$config" -U --needed --noconfirm "$stage"/repo/archlinux-keyring-*.pkg.tar.zst
sudo pacman --config "$config" -Sy --needed --noconfirm "${targets[@]}"
sudo pacman --config "$config" -U --needed --noconfirm greeter/*.pkg.tar.zst
exec_args=(python3 "$bundle/scripts/manage.py" "$action" --offline --package)
"${exec_args[@]}" "$bundle"/desktop/ConsciaDesktop-*.pkg.tar.zst
if [[ $action == install ]]; then
    sudo systemctl enable NetworkManager.service
fi
echo '离线安装完成。请自行重启并选择 Conscia 会话。'
