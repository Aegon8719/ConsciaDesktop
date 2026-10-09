[[ $EUID != 0 ]] || { echo '请以普通用户运行，不要 sudo 整个脚本。' >&2; exit 1; }
source /etc/os-release
case "${ID:-}" in arch|endeavouros) ;; *) echo '目前支持 EndeavourOS / Arch Linux。' >&2; exit 1 ;; esac
[[ $(uname -m) == x86_64 ]] || { echo '目前支持 x86_64。' >&2; exit 1; }
if ! command -v python3 >/dev/null; then
    sudo pacman -Syu --needed --noconfirm python
fi
