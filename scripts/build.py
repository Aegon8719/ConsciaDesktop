#!/usr/bin/env python3
"""Fetch immutable fork revisions into an external build directory and stage a package."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--work", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
lock = json.loads((root / "versions.lock").read_text())
if lock["schema"] != 1 or not re.fullmatch(r"[0-9][0-9.]*", lock["version"]):
    raise SystemExit("Unsupported versions.lock schema/version")
args.work.mkdir(parents=True, exist_ok=True)
args.output.mkdir(parents=True, exist_ok=True)

def run(*command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)

for name in ("niri", "dms"):
    entry = lock[name]
    if not re.fullmatch(r"[0-9a-f]{40}", entry["revision"]):
        raise SystemExit(f"{name}: use a full immutable commit SHA")
    if not entry["repository"].startswith("https://github.com/Aegon8719/"):
        raise SystemExit(f"{name}: expected an Aegon8719 GitHub fork")
    checkout = args.work / name
    if checkout.exists():
        shutil.rmtree(checkout)
    run("git", "init", str(checkout))
    run("git", "remote", "add", "origin", entry["repository"], cwd=checkout)
    run("git", "fetch", "--depth=1", "origin", entry["revision"], cwd=checkout)
    run("git", "checkout", "--detach", entry["revision"], cwd=checkout)
    run("git", "submodule", "update", "--init", "--recursive", cwd=checkout)

os.environ.setdefault("CARGO_BUILD_JOBS", "1")
target = args.work.resolve() / "target"
os.environ.setdefault("CARGO_TARGET_DIR", str(target))
target = Path(os.environ["CARGO_TARGET_DIR"]).resolve()
os.environ["CARGO_PROFILE_RELEASE_DEBUG"] = "0"
os.environ["GOTOOLCHAIN"] = "auto"
run("cargo", "build", "--release", "--locked", cwd=args.work / "niri")
run("make", "build", "VERSION=" + lock["version"], "COMMIT=" + lock["dms"]["revision"], cwd=args.work / "dms")
# Staging must not retain files under paths removed or renamed since the last build.
shutil.rmtree(args.output)
args.output.mkdir(parents=True)
destination = args.output / "usr/lib/ConsciaDesktop"
(destination / "bin").mkdir(parents=True, exist_ok=True)
for source, name in ((target / "release/niri", "niri"),
                     (args.work / "dms/core/bin/dms", "dms"),
                     (args.work / "niri/resources/niri-session", "niri-session")):
    shutil.copy2(source, destination / "bin" / name)
    (destination / "bin" / name).chmod(0o755)
shutil.copytree(root / "scripts", destination / "scripts", dirs_exist_ok=True)
shutil.copytree(root / "config", destination / "config", dirs_exist_ok=True)
shutil.copy2(root / "versions.lock", destination / "versions.lock")
for source, target in ((root / "packages/arch/ConsciaDesktopSession", "usr/bin/ConsciaDesktopSession"),
                       (root / "packages/arch/ConsciaDesktop.desktop", "usr/share/wayland-sessions/ConsciaDesktop.desktop")):
    path = args.output / target
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, path)
    path.chmod(0o755 if target.startswith("usr/bin/") else 0o644)
# Install the forks' session integration without pulling in distribution builds.
for name in ("niri", "dms"):
    path = args.output / "usr/bin" / name
    path.unlink(missing_ok=True)
    path.symlink_to(f"/usr/lib/ConsciaDesktop/bin/{name}")
for source, target in (
    (args.work / "niri/resources/niri.service", "usr/lib/systemd/user/niri.service"),
    (args.work / "niri/resources/niri-shutdown.target", "usr/lib/systemd/user/niri-shutdown.target"),
    (args.work / "niri/resources/niri-portals.conf", "usr/share/xdg-desktop-portal/niri-portals.conf"),
    (args.work / "dms/assets/systemd/dms.service", "usr/lib/systemd/user/dms.service"),
    (args.work / "dms/assets/com.danklinux.dms.svg", "usr/share/icons/hicolor/scalable/apps/com.danklinux.dms.svg"),
):
    path = args.output / target
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, path)
for source in (args.work / "dms/assets").glob("*.desktop"):
    path = args.output / "usr/share/applications" / source.name
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, path)
for name in ("niri", "dms"):
    path = args.output / "usr/share/licenses/ConsciaDesktop" / (name + "-LICENSE")
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.work / name / "LICENSE", path)
