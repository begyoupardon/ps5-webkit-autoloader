#!/usr/bin/env python3
"""Embed Windows console compatibility into the generated standalone host."""

from pathlib import Path
import sys

MARKER = "def _wkal_enable_windows_vt():"
ANCHOR = "\ndef good(text):\n"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: fix_host_console.py <generated-host.py>")
    path = Path(sys.argv[1])
    script = path.read_text(encoding="utf-8")
    if MARKER in script:
        raise SystemExit("Generated host already has Windows console support")
    if script.count(ANCHOR) != 1 or "COLOR = sys.stdout.isatty()" not in script:
        raise SystemExit("Unsupported generated host: console anchors not found")
    runtime = Path(__file__).with_name("host_console_runtime.py").read_text(encoding="utf-8")
    runtime = runtime[runtime.index(MARKER):]
    script = script.replace(ANCHOR, "\n" + runtime + ANCHOR, 1)
    path.write_text(script, encoding="utf-8")


if __name__ == "__main__":
    main()
