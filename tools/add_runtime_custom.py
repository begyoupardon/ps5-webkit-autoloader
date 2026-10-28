#!/usr/bin/env python3
"""Add optional sibling custom/ theme serving to the generated PC host."""
import os
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: add_runtime_custom.py <generated-host.py>")
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as source:
        script = source.read()

    # Keep the adapter tied to the host builder's expected API. Fail the build
    # clearly if upstream changes its generated handler structure.
    import_marker = "from http.server import"
    if import_marker not in script:
        raise SystemExit("Unsupported generated host: HTTP handler import not found")

    # Wrap the generated handler's send_head to serve only known files from
    # <host directory>/custom. This handles the builder's virtual embedded page
    # mapping without changing how its normal requests are resolved.
    script += r'''

# Optional appearance files are served by the generated request handler.
_wkal_allowed = {"theme.json", "custom-theme.css", "custom-logo.svg", "custom-logo.png", "custom-logo.webp"}
_wkal_parent = os.path.dirname(os.path.abspath(sys.argv[0]))
_wkal_handler_class = None
for _wkal_name, _wkal_value in list(globals().items()):
    if (isinstance(_wkal_value, type) and hasattr(_wkal_value, "send_head")
            and "Handler" in _wkal_name and hasattr(_wkal_value, "__mro__")
            and any(base.__module__ == "http.server" for base in _wkal_value.__mro__[1:])):
        _wkal_handler_class = _wkal_value
        break
if _wkal_handler_class is None:
    raise SystemExit("Unsupported generated host: request handler class not found")
_wkal_original_send_head = _wkal_handler_class.send_head
def _wkal_send_head(self):
    from urllib.parse import urlsplit
    import mimetypes
    name = urlsplit(self.path).path.rsplit("/", 1)[-1]
    if name in _wkal_allowed:
        candidate = os.path.join(_wkal_parent, "custom", name)
        if os.path.isfile(candidate):
            try:
                file = open(candidate, "rb")
            except OSError:
                self.send_error(404, "Custom theme file unavailable")
                return None
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(candidate)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(os.path.getsize(candidate)))
            self.end_headers()
            return file
    return _wkal_original_send_head(self)
_wkal_handler_class.send_head = _wkal_send_head
'''
    # The patched handler uses these standard-library modules.
    if "import os\n" not in script:
        script = script.replace(import_marker, "import os\n" + import_marker, 1)
    if "import sys\n" not in script:
        script = script.replace(import_marker, "import sys\n" + import_marker, 1)
    with open(path, "w", encoding="utf-8") as output:
        output.write(script)


if __name__ == "__main__":
    main()
