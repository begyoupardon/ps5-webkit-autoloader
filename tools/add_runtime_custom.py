#!/usr/bin/env python3
"""Embed optional sibling custom/ branding into generated PC setup pages.

The PC host serves standalone HTML from an in-memory ZIP. Its setup pages do not
request theme files, and the PS5's later installer uses a different server.
Patch only the host's HTML response, keeping exploit bytes and routing intact.
"""
import os
import sys

MARKER = "# WKAL optional runtime setup-page branding"
ENTRY = '\nif __name__ == "__main__":\n    sys.exit(main())\n'

ADAPTER = r'''

# WKAL optional runtime setup-page branding
_wkal_custom_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "custom")
_wkal_original_resolve = GuideHandler._resolve

def _wkal_read_file(name, limit):
    path = os.path.join(_wkal_custom_dir, name)
    try:
        if os.path.getsize(path) > limit:
            return None
        with open(path, "rb") as source:
            return source.read()
    except OSError:
        return None

def _wkal_theme_parts():
    import json
    import base64
    import re
    raw = _wkal_read_file("theme.json", 16384)
    try:
        theme = json.loads(raw) if raw else {}
    except (ValueError, UnicodeError):
        theme = {}
    if not isinstance(theme, dict):
        theme = {}
    safe = {}
    for key in ("title", "brand"):
        value = theme.get(key)
        if isinstance(value, str) and 0 < len(value) <= 120:
            safe[key] = value
    colors = theme.get("colors")
    if isinstance(colors, dict):
        safe["colors"] = {
            key: value for key, value in colors.items()
            if key in ("background", "surface", "border", "text", "muted", "accent", "accentEnd")
            and isinstance(value, str)
            and re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", value)
        }
    logo = theme.get("logo", "/logo.svg")
    # Accept the earlier JSON spelling while the file itself stays logo.svg.
    if logo == "/custom-logo.svg":
        logo = "/logo.svg"
    if logo in ("/logo.svg", "/logo.png", "/logo.webp"):
        ext = logo.rsplit(".", 1)[-1]
        data = _wkal_read_file("logo." + ext, 262144)
        if data:
            mime = {"svg": "image/svg+xml", "png": "image/png", "webp": "image/webp"}[ext]
            safe["logoSrc"] = "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
    css = _wkal_read_file("theme.css", 32768)
    if css:
        try:
            css = css.decode("utf-8")
            if re.search(r"</style", css, re.IGNORECASE):
                css = ""
        except UnicodeError:
            css = ""
    else:
        css = ""
    return safe, css

def _wkal_resolve(self):
    resolved = _wkal_original_resolve(self)
    if not resolved or resolved[2] not in ("index.html", "poops.html", "relapse.html"):
        return resolved
    kind, full, shown, data, mtime = resolved
    if kind == "file":
        try:
            with open(full, "rb") as source:
                data = source.read()
        except OSError:
            return resolved
    if not data or b"</head>" not in data:
        return resolved
    theme, css = _wkal_theme_parts()
    if not theme and not css:
        return resolved
    import json
    theme_json = json.dumps(theme, ensure_ascii=True, separators=(",", ":"))
    theme_json = theme_json.replace("<", "\\u003c").replace(">", "\\u003e")
    markup = '<script>window.WKAL_THEME=' + theme_json + ';</script>'
    if css:
        markup += '<style id="wkal-custom-theme">' + css + '</style>'
    data = data.replace(b"</head>", markup.encode("utf-8") + b"</head>", 1)
    return "zip", None, shown, data, mtime

GuideHandler._resolve = _wkal_resolve
_wkal_initial_theme, _wkal_initial_css = _wkal_theme_parts()
if _wkal_initial_theme.get("brand"):
    HOST_NAME = _wkal_initial_theme["brand"]
'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: add_runtime_custom.py <generated-host.py>")
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as source:
        script = source.read()
    if MARKER in script:
        raise SystemExit("Generated host already has runtime branding support")
    if "class GuideHandler(SimpleHTTPRequestHandler):" not in script:
        raise SystemExit("Unsupported generated host: GuideHandler not found")
    entry_pos = script.rfind(ENTRY)
    if entry_pos < 0:
        raise SystemExit("Unsupported generated host: entry point not found")
    script = script[:entry_pos] + ADAPTER + script[entry_pos:]
    with open(path, "w", encoding="utf-8") as output:
        output.write(script)


if __name__ == "__main__":
    main()
