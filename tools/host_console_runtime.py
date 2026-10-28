"""Console compatibility code embedded into the standalone PC host.

Keep this file self-contained: fix_host_console.py copies its body into the
generated host, which cannot import project files when distributed alone.
"""

def _wkal_enable_windows_vt():
    """Use ANSI colors only after Windows accepts virtual terminal output."""
    global COLOR
    if os.name != "nt":
        return
    if not sys.stdout.isatty():
        COLOR = False
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if handle in (0, -1) or not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            COLOR = False
        elif not kernel32.SetConsoleMode(handle, mode.value | 0x0004):
            COLOR = False
    except Exception:
        # Console decoration must never stop DNS/HTTP hosting.
        COLOR = False


_wkal_enable_windows_vt()

_WKAL_ASCII_BORDER = str.maketrans({"┌": "+", "┐": "+", "└": "+", "┘": "+", "─": "-", "│": "|"})


def say(text):
    """Keep Windows borders legible and survive legacy output encodings."""
    if os.name == "nt":
        text = text.translate(_WKAL_ASCII_BORDER)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(text, flush=True)
