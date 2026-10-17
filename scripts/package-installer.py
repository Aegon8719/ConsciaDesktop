#!/usr/bin/env python3
"""Generate the online entrypoint for the same bundle used by offline installs."""
import json
from pathlib import Path
import shlex

root = Path(__file__).resolve().parent.parent
version = json.loads((root / "versions.lock").read_text())["version"]
script = (root / "scripts/install-release.sh").read_text()
script = script.replace("set -euo pipefail", "set -euo pipefail\nexport CONSCIA_RELEASE_VERSION=" + shlex.quote(version), 1)
output = root / "dist/ConsciaDesktop-EndeavourOS.run"
output.parent.mkdir(parents=True, exist_ok=True)
temporary = output.with_suffix(".tmp")
temporary.write_text(script)
temporary.chmod(0o755)
temporary.replace(output)
print(f"Created {output} for Release v{version}")
