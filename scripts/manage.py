#!/usr/bin/env python3
"""Single-user desktop lifecycle; pacman owns binaries, snapshots own user configuration."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
store = state / "conscia-desktop"
database = store / "installation.json"
pending = store / "pending.json"
owner = Path("/var/lib/conscia-desktop/owner")
units = config / "systemd/user"
managed = [config / "niri", config / "DankMaterialShell", state / "DankMaterialShell/session.json",
           cache / "DankMaterialShell/dms-colors.json", data / "conscia/assets",
           units / "niri.service.d/90-conscia-local.conf", units / "dms.service.d/90-conscia-local.conf",
           units / "conscia-focus-gradient.service", units / "conscia-focus-gradient.path",
           units / "niri.service.wants/dms.service",
           units / "default.target.wants/conscia-focus-gradient.path",
           units / "default.target.wants/conscia-focus-gradient.service",
           units / "sockets.target.wants/pipewire.socket",
           units / "sockets.target.wants/pipewire-pulse.socket",
           units / "pipewire.service.wants/wireplumber.service"]

def run(*command, **kwargs):
    return subprocess.run([str(arg) for arg in command], check=True, **kwargs)

def output(*command):
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)

def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)

def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target, follow_symlinks=False)

def snapshot(destination):
    records = []
    for index, path in enumerate(managed):
        exists = path.exists() or path.is_symlink()
        records.append({"path": str(path), "exists": exists, "file": str(index)})
        if exists:
            copy(path, destination / str(index))
    save(destination / "index.json", records)

def restore(destination):
    for record in json.loads((destination / "index.json").read_text()):
        path = Path(record["path"])
        remove(path)
        if record["exists"]:
            copy(destination / record["file"], path)

def reload_user():
    run("systemctl", "--user", "daemon-reload")

def stop_gradient():
    for suffix in ("path", "service"):
        subprocess.run(["systemctl", "--user", "stop", "conscia-focus-gradient." + suffix], check=False)

def resume_gradient():
    reload_user()
    for suffix in ("path", "service"):
        if (units / ("default.target.wants/conscia-focus-gradient." + suffix)).exists():
            run("systemctl", "--user", "start", "conscia-focus-gradient." + suffix)

def recover(transaction):
    stop_gradient()
    old = transaction["old"]
    if old:
        run("sudo", "pacman", "-U", "--noconfirm", old["history"][-1])
    elif output("pacman", "-Q", "conscia-desktop").returncode == 0:
        run("sudo", "pacman", "-R", "--noconfirm", "conscia-desktop")
    restore(Path(transaction["snapshot"]))
    if transaction.get("enabled_sddm"):
        run("sudo", "systemctl", "enable" if transaction["sddm_enabled"] else "disable", "sddm.service")
        run("sudo", "systemctl", "set-default", transaction["default_target"])
    if old:
        save(database, old)
        identity = store / "owner"
        identity.write_text(str(os.getuid()) + "\n")
        run("sudo", "install", "-Dm644", identity, owner)
    else:
        database.unlink(missing_ok=True)
        run("sudo", "rm", "-f", str(owner))
    resume_gradient()
    pending.unlink(missing_ok=True)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=("install", "update", "rollback", "uninstall"))
parser.add_argument("--package", type=Path, help="install a prebuilt Arch package instead of compiling")
parser.add_argument("--recover", action="store_true", help="recover an interrupted transaction")
args = parser.parse_args()
if args.package and args.action not in ("install", "update"):
    parser.error("--package is only valid for install/update")
if os.geteuid() == 0:
    raise SystemExit("请以普通用户运行；脚本仅在需要时调用 sudo。")
if not Path("/etc/arch-release").exists():
    raise SystemExit("目前支持 EndeavourOS / Arch Linux。")
if owner.exists() and owner.read_text().strip() != str(os.getuid()):
    raise SystemExit("该机器上的 Conscia 由另一个用户管理，请由原安装用户操作。")
if any(output("systemctl", "--user", "is-active", "--quiet", unit).returncode == 0
       for unit in ("niri.service", "dms.service")):
    raise SystemExit("请注销 niri/DMS，改在本机 TTY 中运行此命令。")
run("systemctl", "--user", "show-environment", stdout=subprocess.DEVNULL)
run("sudo", "-v")
store.mkdir(parents=True, exist_ok=True)
# One lifecycle operation at a time, including dependency installation and compilation.
import fcntl
guard = (store / "operation.lock").open("w")
fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
if args.recover:
    if args.action != "rollback" or not pending.exists():
        raise SystemExit("没有可恢复的中断事务。")
    recover(json.loads(pending.read_text()))
    raise SystemExit("已恢复中断前的程序与配置。")
if pending.exists():
    raise SystemExit("上次事务尚未完成，请先运行 bash rollback.sh --recover。")
old = json.loads(database.read_text()) if database.exists() else None
installed = output("pacman", "-Q", "conscia-desktop").returncode == 0
if args.action == "install" and (old or installed):
    raise SystemExit("已有安装。通过本安装器安装的版本请运行 update.sh；手动安装的软件包请先卸载。")
if args.action != "install" and not old:
    raise SystemExit("找不到本用户的安装记录。")
if args.action == "rollback" and len(old["history"]) < 2:
    raise SystemExit("没有可回退的旧软件包；至少需要完成一次更新。")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
package = None
if args.action in ("install", "update"):
    run("sudo", "pacman", "-Syu", "--needed", "--noconfirm", "base-devel", "git", "python")
    if args.package:
        package = args.package.resolve(strict=True)
        info = output("pacman", "-Qp", str(package))
        if info.returncode or info.stdout.split()[0] != "conscia-desktop":
            raise SystemExit("--package 必须指向 conscia-desktop Arch 软件包。")
    else:
        work = cache / "conscia-desktop/builds" / stamp
        work.mkdir(parents=True)
        makepkg_config = work / "makepkg.conf"
        makepkg_config.write_text("source /etc/makepkg.conf\n" +
            f"BUILDDIR={shlex.quote(str(work / 'build'))}\nPKGDEST={shlex.quote(str(work))}\n")
        run("makepkg", "--config", makepkg_config, "--syncdeps", "--noconfirm", "--nocheck",
            cwd=root / "packages/arch")
        packages = list(work.glob("conscia-desktop-*.pkg.tar.*"))
        package = next(path for path in packages if not path.name.endswith(".sig"))
    cached = store / "packages" / stamp / package.name
    cached.parent.mkdir(parents=True)
    shutil.copy2(package, cached)
    package = cached

transaction_dir = store / "snapshots" / stamp
stop_gradient()
snapshot(transaction_dir)
transaction = {"old": old, "snapshot": str(transaction_dir), "enabled_sddm": False,
               "sddm_enabled": output("systemctl", "is-enabled", "--quiet", "sddm.service").returncode == 0,
               "default_target": output("systemctl", "get-default").stdout.strip()}
save(pending, transaction)
try:
    if args.action in ("install", "update"):
        run("sudo", "pacman", "-U", "--noconfirm", package)
        record = old or {"history": [], "baseline": str(transaction_dir), "enabled_sddm": False,
                         "default_target": transaction["default_target"]}
        if args.action == "install":
            run("python3", "/usr/lib/conscia/scripts/deploy-profile.py",
                "/usr/lib/conscia/config", transaction_dir / "deployment")
            reload_user()
            run("systemctl", "--user", "add-wants", "niri.service", "dms.service")
            run("systemctl", "--user", "enable", "conscia-focus-gradient.path", "conscia-focus-gradient.service")
            run("systemctl", "--user", "enable", "pipewire.socket", "pipewire-pulse.socket", "wireplumber.service")
            if not Path("/etc/systemd/system/display-manager.service").exists():
                run("sudo", "pacman", "-S", "--needed", "--noconfirm", "sddm", "xorg-server")
                transaction["enabled_sddm"] = record["enabled_sddm"] = True
                save(pending, transaction)
                run("sudo", "systemctl", "enable", "sddm.service")
                run("sudo", "systemctl", "set-default", "graphical.target")
            identity = store / "owner"
            identity.write_text(str(os.getuid()) + "\n")
            run("sudo", "install", "-Dm644", identity, owner)
        record = dict(record, history=[*record["history"], str(package)])
        save(database, record)
    elif args.action == "rollback":
        run("sudo", "pacman", "-U", "--noconfirm", old["history"][-2])
        save(database, dict(old, history=old["history"][:-1]))
    else:
        run("sudo", "pacman", "-R", "--noconfirm", "conscia-desktop")
        restore(Path(old["baseline"]))
        if old["enabled_sddm"] and Path("/etc/systemd/system/display-manager.service").resolve().name == "sddm.service":
            transaction["enabled_sddm"] = True
            save(pending, transaction)
            run("sudo", "systemctl", "disable", "sddm.service")
            run("sudo", "systemctl", "set-default", old["default_target"])
        database.unlink()
        run("sudo", "rm", "-f", owner)
    resume_gradient()
    pending.unlink()
except Exception:
    print("操作失败，正在恢复操作前的软件包和个人配置。")
    recover(transaction)
    raise
print(f"{args.action} 完成。配置备份和软件包历史：{store}")
print("不会自动注销或重启。系统依赖及其升级不会被回退。")
if args.action != "uninstall":
    print("下次登录时选择 Conscia。")
