#!/usr/bin/env python3
"""Generate PS5 and Windows icons from the stock or optional custom SVG.

The stock sphere uses its existing padded wrapper. A custom/logo.svg mark is
fitted inside a square tile with 10% safe padding and a theme color background.

Outputs:
  assets/icon0.png                        PS5 homescreen icon (512x512)
  assets/icon.ico                         Windows .exe icon (16-256px)

Rendering: rsvg-convert when available (installed in the ps5-webkit-autoloader-sdk
docker image), qlmanage as the built-in macOS fallback. Run via `make icons`.
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from theme_config import load_theme

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MASTER = os.path.join(ROOT, "assets", "icon.svg")
CUSTOM_MASTER = os.path.join(ROOT, "custom", "logo.svg")
ICON0 = os.path.join(ROOT, "assets", "icon0.png")
ICON_ICO = os.path.join(ROOT, "assets", "icon.ico")

VIEWBOX = 1024
ART_RADIUS = 510.04  # outermost extent of the master art (ring reaches y=1022.08)
PAD_FRACTION = 0.1
SCALE = (1.0 - 2.0 * PAD_FRACTION) * (VIEWBOX / 2.0) / ART_RADIUS
TRANSLATE = VIEWBOX * (1.0 - SCALE) / 2.0
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

BG_GRADIENT = """    <radialGradient id="wkalBg" cx="50%" cy="50%" r="75%">
      <stop offset="0%" stop-color="#0e182b"/>
      <stop offset="100%" stop-color="#060a13"/>
    </radialGradient>"""


def build_wrapper_svg(master_src):
    """Master SVG re-wrapped with a dark background and ~10% padding."""
    defs = re.search(r"<defs>(.*?)</defs>", master_src, re.S)
    art = re.search(r"</defs>(.*?)</svg>", master_src, re.S)
    if not defs or not art:
        sys.exit("Error: could not parse master icon.svg (defs/art not found).")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {vb} {vb}">\n'
        "  <defs>\n"
        "{bg}\n"
        "{defs}\n"
        "  </defs>\n"
        '  <rect width="{vb}" height="{vb}" fill="url(#wkalBg)"/>\n'
        '  <g transform="translate({t} {t}) scale({s})">\n'
        "{art}\n"
        "  </g>\n"
        "</svg>\n"
    ).format(
        vb=VIEWBOX,
        bg=BG_GRADIENT,
        defs=defs.group(1).strip(),
        art=art.group(1).strip(),
        t=round(TRANSLATE, 3),
        s=round(SCALE, 6),
    )


def build_custom_wrapper_svg(path):
    """Fit a supplied SVG mark inside a square tile with 10% safe padding."""
    svg_ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_ns)
    root = ET.parse(path).getroot()
    if root.tag != "{%s}svg" % svg_ns:
        raise ValueError("custom/logo.svg must have an SVG root element")
    # Nested SVG preserves the mark's own viewBox, fill and proportions.
    root.set("x", "102")
    root.set("y", "102")
    root.set("width", "820")
    root.set("height", "820")
    theme = load_theme()
    background = theme.get("colors", {}).get("accentEnd", "#0f172a")
    return (
        '<svg xmlns="%s" viewBox="0 0 1024 1024">'
        '<rect width="1024" height="1024" fill="%s"/>'
        '%s</svg>'
    ) % (svg_ns, background, ET.tostring(root, encoding="unicode"))


def rsvg_render(svg_path, size):
    """Render the SVG to PNG bytes at the given size via rsvg-convert."""
    return subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), svg_path],
        check=True,
        capture_output=True,
    ).stdout


def ql_render(svg_path, size):
    """Render via QuickLook; use a unique temp filename to dodge its cache."""
    tmpdir = tempfile.mkdtemp(prefix="wkal-icon-")
    tmp_svg = os.path.join(tmpdir, os.urandom(4).hex() + ".svg")
    shutil.copyfile(svg_path, tmp_svg)
    subprocess.run(["qlmanage", "-t", "-s", str(size), "-o", tmpdir, tmp_svg],
                   check=True, capture_output=True)
    rendered = os.path.join(tmpdir, os.path.basename(tmp_svg) + ".png")
    with open(rendered, "rb") as f:
        return f.read()


def find_renderer():
    if shutil.which("rsvg-convert"):
        return rsvg_render
    if sys.platform == "darwin" and shutil.which("qlmanage"):
        return ql_render
    sys.exit(
        "Error: no SVG renderer found.\n"
        "  Run the build inside the ps5-webkit-autoloader-sdk docker image "
        "(has rsvg-convert),\n"
        "  or use macOS where qlmanage is available."
    )


def build_ico(pngs):
    """Assemble PNG blobs into a Windows .ico (Vista+ PNG-in-ICO format)."""
    header = struct.pack("<HHH", 0, 1, len(pngs))
    entries = b""
    offset = 6 + 16 * len(pngs)
    for size, data in pngs:
        w = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return header + entries + b"".join(data for _, data in pngs)


def main():
    if os.path.isfile(CUSTOM_MASTER):
        wrapper = build_custom_wrapper_svg(CUSTOM_MASTER)
        source = "custom/logo.svg"
    else:
        with open(MASTER, "r") as f:
            master_src = f.read()
        wrapper = build_wrapper_svg(master_src)
        source = "assets/icon.svg"
    render = find_renderer()

    with tempfile.TemporaryDirectory(prefix="wkal-icon-") as tmp:
        wrapper_path = os.path.join(tmp, "icon-bg.svg")
        with open(wrapper_path, "w") as f:
            f.write(wrapper)

        # PS5 homescreen icon (512x512) and Windows .exe icon (16-256px)
        with open(ICON0, "wb") as f:
            f.write(render(wrapper_path, 512))
        pngs = [(size, render(wrapper_path, size)) for size in ICO_SIZES]
        with open(ICON_ICO, "wb") as f:
            f.write(build_ico(pngs))

    print("Generated icon assets from %s:" % source)
    for path in (ICON0, ICON_ICO):
        print(f"  {os.path.relpath(path, ROOT)} ({os.path.getsize(path)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
