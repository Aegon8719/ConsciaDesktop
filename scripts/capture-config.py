#!/usr/bin/env python3
"""Capture Conscia preferences only; never vendor compositor or shell sources."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

root = Path(__file__).resolve().parent.parent
home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
with tempfile.TemporaryDirectory(prefix="conscia-config-") as directory:
    profile = Path(directory) / "profile"
    assets = profile / "assets"
    assets.mkdir(parents=True)
    asset_map = {}

    def portable(value):
        if isinstance(value, str):
            original = value
            raw = value.removeprefix("file://")
            path = Path(raw)
            if path.is_absolute() and path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif", ".avif"):
                if path.is_file():
                    if raw not in asset_map:
                        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
                        name = digest + path.suffix.lower()
                        shutil.copy2(path, assets / name)
                        asset_map[raw] = "@CONSCIA_DATA@/assets/" + name
                    value = ("file://" if original.startswith("file://") else "") + asset_map[raw]
                else:
                    print(f"资源不存在，保留待迁移路径：{raw}")
            return value.replace(str(home), "@CONSCIA_HOME@")
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, dict):
            return {portable(key): portable(item) for key, item in value.items()}
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
    palette = cache / "DankMaterialShell/dms-colors.json"
    if palette.exists():
        shutil.copy2(palette, profile / palette.name)
    manifest = {
        "created": datetime.now().astimezone().isoformat(),
        "target": "EndeavourOS / Arch Linux x86_64",
        "source": "Conscia desktop preferences",
        "assets": list(asset_map.values()),
        "tests_run": False,
    }
    (profile / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    destination = root / "config"
    for source in profile.iterdir():
        target = destination / source.name
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    print(f"Captured desktop preferences: {destination}")
