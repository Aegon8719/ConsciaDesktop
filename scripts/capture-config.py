#!/usr/bin/env python3
"""Capture Conscia preferences only; never vendor compositor or shell sources."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile

root = Path(__file__).resolve().parent.parent
home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
with tempfile.TemporaryDirectory(prefix="conscia-config-") as directory:
    profile = Path(directory) / "profile"
    profile.mkdir(parents=True)

    def portable(value):
        if isinstance(value, str):
            return value.replace(str(home), "@CONSCIA_HOME@")
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, dict):
            return {portable(key): portable(item) for key, item in value.items()
                    if "wallpaper" not in key.lower() or key == "blurWallpaperOnOverview"}
        return value

    # Capture active preferences, not historical backups, clipboard data or account state.
    niri = profile / "niri"
    niri.mkdir(parents=True)
    for path in (config / "niri").rglob("*.kdl"):
        relative = path.relative_to(config / "niri")
        target = niri / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(path.read_text().replace(str(home), "@CONSCIA_HOME@"))
    dms = profile / "DankMaterialShell"
    dms.mkdir(parents=True)
    for name in ("settings.json", "plugin_settings.json", ".firstlaunch"):
        source = config / "DankMaterialShell" / name
        if not source.exists():
            continue
        if source.suffix == ".json":
            content = portable(json.loads(source.read_text()))
            (dms / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n")
        else:
            shutil.copy2(source, dms / name)
    session_source = state / "DankMaterialShell/session.json"
    session = json.loads(session_source.read_text()) if session_source.exists() else {}
    for key in ("launcherQueryHistory", "lastPlayerIdentity"):
        session.pop(key, None)
    (profile / "session.json").write_text(json.dumps(portable(session), ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "created": datetime.now().astimezone().isoformat(),
        "target": "EndeavourOS / Arch Linux x86_64",
        "source": "Conscia desktop preferences",
    }
    (profile / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    destination = root / "config"
    shutil.rmtree(destination / "assets", ignore_errors=True)
    (destination / "dms-colors.json").unlink(missing_ok=True)
    for source in profile.iterdir():
        target = destination / source.name
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    print(f"Captured desktop preferences: {destination}")
