#!/usr/bin/env python3
"""Apply DMS Material You colors to niri's focus gradient on palette changes."""

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile


def linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def rgb(color):
    if not isinstance(color, str) or len(color) != 7 or not color.startswith("#"):
        raise ValueError("expected an opaque #RRGGBB palette color")
    return tuple(linear(int(color[i:i + 2], 16) / 255) for i in (1, 3, 5))


# Public-domain sRGB/Oklab matrices: https://bottosson.github.io/posts/oklab/
def oklch(color):
    r, g, b = color
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    lightness = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return lightness, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def from_oklch(lightness, chroma, hue):
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def luminance(color):
    return sum(c * weight for c, weight in zip(color, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    a, b = luminance(a), luminance(b)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def to_hex(color):
    def encode(value):
        value = min(1., max(0., value))
        value = 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055
        return round(value * 255)
    return "#" + "".join(f"{encode(value):02x}" for value in color)


def gradient(colors, mode):
    primary = oklch(rgb(colors["primary"]))
    tertiary = oklch(rgb(colors.get("tertiary", colors["primary"])))
    source = rgb(colors.get("source_color", colors["primary"]))
    source_lch = oklch(source)
    hue = primary[2] if primary[1] >= 0.025 else source_lch[2]
    if max(primary[1], source_lch[1]) < 0.025:
        hue = 250.
    delta = (tertiary[2] - hue + 180.) % 360. - 180.
    # Keep the Material You accent relationship within a coherent, visible arc.
    delta = math.copysign(min(75., max(30., abs(delta))), delta or 1.)
    neutral = max(primary[1], tertiary[1], source_lch[1]) < 0.025
    chroma = 0.08 if neutral else min(0.22, max(0.15, primary[1] * 1.2))
    end_chroma = 0.08 if neutral else min(0.22, max(0.15, tertiary[1] * 1.2))
    backgrounds = [rgb(colors[key]) for key in
                   ("background", "surface", "surface_container", "surface_container_highest")
                   if key in colors]
    if not backgrounds:
        raise ValueError("palette has no surface colors")
    preferred = 0.76 if mode == "dark" else 0.53
    levels = range(58, 91) if mode == "dark" else range(30, 66)
    best = None
    for level in levels:
        lightness = level / 100

        def samples(factor):
            return [from_oklch(lightness - 0.025 * t,
                               (chroma + (end_chroma - chroma) * t) * factor,
                               hue + delta * t) for t in (i / 16 for i in range(17))]

        # Reduce chroma instead of clipping RGB channels and shifting the hue.
        low, high = 0., 1.
        for _ in range(14):
            middle = (low + high) / 2
            if all(0 <= channel <= 1 for color in samples(middle) for channel in color):
                low = middle
            else:
                high = middle
        ramp = samples(low)
        minimum = min(contrast(color, bg) for color in ramp for bg in backgrounds)
        wallpaper = min(contrast(color, source) for color in ramp)
        score = (min(minimum / 3., 1.),
                 low - abs(lightness - preferred) * 0.8 + min(wallpaper, 3.) * 0.04,
                 minimum)
        if best is None or score > best[0]:
            best = score, to_hex(ramp[0]), to_hex(ramp[-1])
    return best[1], best[2]


def apply(palette, output):
    data = json.loads(palette.read_text())
    mode = data["mode"]
    if mode not in ("dark", "light"):
        raise ValueError("unknown DMS palette mode")
    colors = data["colors"][mode]
    start, end = gradient(colors, mode)
    # Preserve the quieter Material You outline and the urgent color.
    inactive = to_hex(rgb(colors["outline"]))
    urgent = to_hex(rgb(colors["error"]))
    blocks = []
    for name in ("focus-ring", "border"):
        blocks.append(f'''    {name} {{
        active-gradient from="{start}" to="{end}" angle=45 in="oklch shorter hue"
        inactive-color "{inactive}"
        urgent-color "{urgent}"
    }}''')
    content = ("// Generated from the DMS wallpaper palette by update-focus-gradient.py.\n"
               + "layout {\n" + "\n".join(blocks) + "\n}\n")
    if output.exists() and output.read_text() == content:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
        temporary.chmod(0o644)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Applied {mode} wallpaper focus gradient: {start} → {end}")


def main():
    home = Path.home()
    cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
    config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--palette", type=Path, default=cache / "DankMaterialShell/dms-colors.json")
    parser.add_argument("--output", type=Path, default=config / "niri/ConsciaDesktop/appearance.kdl")
    args = parser.parse_args()
    try:
        apply(args.palette, args.output)
    except (FileNotFoundError, ValueError, KeyError, TypeError) as error:
        # Keep the last working border if a theme update is incomplete.
        print(f"Keeping previous focus gradient: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
