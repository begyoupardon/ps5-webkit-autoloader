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

    # Install the adapter before the host's entry point starts its servers.
    entry = '\nif __name__ == "__main__":\n    sys.exit(main())\n'
    if script.rfind(entry) < 0:
        raise SystemExit("Unsupported generated host: executable entry point not found")
    adapter = r'''

# Optional appearance files are served by the generated request handler.
_wkal_allowed = {"theme.json", "theme.css", "logo.svg", "logo.png", "logo.webp"}
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
    entry_pos = script.rfind(entry)
    script = script[:entry_pos] + adapter + script[entry_pos:]
    with open(path, "w", encoding="utf-8") as output:
        output.write(script)


if __name__ == "__main__":
    main()
