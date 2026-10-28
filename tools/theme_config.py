"""Read optional build-time branding from custom/ without network resources."""
import base64
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM = os.path.join(ROOT, "custom")
HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\Z")
COLOR_KEYS = ("background", "backgroundEnd", "surface", "border", "text", "muted", "accent", "accentEnd")
LOGO_TYPES = {"svg": "image/svg+xml", "png": "image/png", "webp": "image/webp"}


def load_theme():
    path = os.path.join(CUSTOM, "theme.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as source:
        theme = json.load(source)
    if not isinstance(theme, dict):
        raise ValueError("custom/theme.json must be a JSON object")
    clean = {}
    for key in ("title", "brand"):
        value = theme.get(key)
        if value is not None:
            if not isinstance(value, str) or not 0 < len(value.strip()) <= 120:
                raise ValueError("custom/theme.json: %s must be nonempty text up to 120 characters" % key)
            clean[key] = value.strip()
    colors = theme.get("colors", {})
    if not isinstance(colors, dict):
        raise ValueError("custom/theme.json: colors must be an object")
    clean["colors"] = {}
    for key in COLOR_KEYS:
        if key in colors:
            value = colors[key]
            if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
                raise ValueError("custom/theme.json: colors.%s must be a CSS hex color" % key)
            clean["colors"][key] = value
    logo = theme.get("logo")
    if logo is not None:
        if logo not in ("/logo.svg", "/logo.png", "/logo.webp"):
            raise ValueError("custom/theme.json: logo must be /logo.svg, /logo.png, or /logo.webp")
        clean["logo"] = logo
    return clean


def logo_data_uri(theme):
    logo = theme.get("logo")
    if not logo:
        return None
    filename = logo.lstrip("/")
    path = os.path.join(CUSTOM, filename)
    if not os.path.isfile(path):
        raise ValueError("custom/theme.json references missing custom/%s" % filename)
    if os.path.getsize(path) > 262144:
        raise ValueError("custom/%s exceeds the 256 KiB logo limit" % filename)
    ext = filename.rsplit(".", 1)[-1]
    with open(path, "rb") as source:
        encoded = base64.b64encode(source.read()).decode("ascii")
    return "data:%s;base64,%s" % (LOGO_TYPES[ext], encoded)
