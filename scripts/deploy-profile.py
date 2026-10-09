#!/usr/bin/env python3
"""Install a captured profile for the invoking user, retaining prior files."""
import json
import os
from pathlib import Path
import shutil
import sys

profile, backup = map(Path, sys.argv[1:])
home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
replacements = {"@CONSCIA_HOME@": str(home), "@CONSCIA_DATA@": str(data / "conscia")}

def replace(value):
    if isinstance(value, str):
        for old, new in replacements.items():
            value = value.replace(old, new)
    elif isinstance(value, list):
        value = [replace(item) for item in value]
    elif isinstance(value, dict):
        value = {replace(key): replace(item) for key, item in value.items()}
    return value

def save_old(path, label):
    if not path.exists() and not path.is_symlink():
        return
    destination = backup / "user" / label
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir() and not path.is_symlink():
        shutil.copytree(path, destination, symlinks=True)
    else:
        shutil.copy2(path, destination, follow_symlinks=False)

def write(path, content, label):
    save_old(path, label)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".conscia-new")
    temporary.write_text(content)
    os.replace(temporary, path)

assets = data / "conscia/assets"
assets.mkdir(parents=True, exist_ok=True)
shutil.copytree(profile / "assets", assets, dirs_exist_ok=True)
for name in ("niri", "DankMaterialShell"):
    target = config / name
    save_old(target, "config/" + name)
    staged = config / (name + ".conscia-new")
    if staged.exists():
        raise RuntimeError(f"unfinished earlier installation: {staged}")
    shutil.copytree(profile / name, staged)
    for path in staged.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".json":
            path.write_text(json.dumps(replace(json.loads(path.read_text())), ensure_ascii=False, indent=2) + "\n")
        elif path.suffix in (".kdl", ".css", ".conf"):
            text = path.read_text()
            text = text.replace('XDG_MENU_PREFIX "plasma-"', 'XDG_MENU_PREFIX "arch-"')
            for old, new in replacements.items():
                text = text.replace(old, json.dumps(new, ensure_ascii=False)[1:-1])
            path.write_text(text)
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        shutil.rmtree(target)
    os.replace(staged, target)

session = replace(json.loads((profile / "session.json").read_text()))
write(state / "DankMaterialShell/session.json", json.dumps(session, ensure_ascii=False, indent=2) + "\n", "state/session.json")
if (profile / "dms-colors.json").exists():
    write(cache / "DankMaterialShell/dms-colors.json", (profile / "dms-colors.json").read_text(), "cache/dms-colors.json")

units = config / "systemd/user"
for name in ("niri", "dms"):
    args = "--session" if name == "niri" else "run --session"
    content = f"[Service]\nEnvironment=PATH=/usr/lib/conscia/bin:/usr/local/bin:/usr/bin\nExecStart=\nExecStart=/usr/lib/conscia/bin/{name} {args}\n"
    write(units / f"{name}.service.d/90-conscia-local.conf", content, f"units/{name}.conf")

def quote(path):
    return '"' + str(path).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'

palette = cache / "DankMaterialShell/dms-colors.json"
appearance = config / "niri/conscia/appearance.kdl"
service = f'''[Unit]
Description=Conscia wallpaper focus gradient
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/lib/conscia/scripts/update-focus-gradient.py --palette {quote(palette)} --output {quote(appearance)}
TimeoutStartSec=15
[Install]
WantedBy=default.target
'''
path_unit = f'''[Unit]
Description=Watch the DMS wallpaper palette
[Path]
PathChanged={str(palette).replace('%', '%%')}
Unit=conscia-focus-gradient.service
[Install]
WantedBy=default.target
'''
for suffix, content in (("service", service), ("path", path_unit)):
    write(units / f"conscia-focus-gradient.{suffix}", content, f"units/focus-gradient.{suffix}")
(home / "Pictures/Screenshots").mkdir(parents=True, exist_ok=True)
