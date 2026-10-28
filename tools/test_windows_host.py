#!/usr/bin/env python3
"""Smoke-test the packaged Windows host's startup and redirected console text."""

from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: test_windows_host.py <host.exe|host.py>")
    exe = Path(sys.argv[1]).resolve()
    if not exe.is_file():
        raise SystemExit(f"Missing host executable: {exe}")

    command = [sys.executable, str(exe)] if exe.suffix == ".py" else [str(exe)]
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            command + ["--ip", "127.0.0.1", "--no-dns", "--no-https", "--http-port", "0"],
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                output.seek(0)
                log = output.read().decode("utf-8", errors="replace")
                if "Waiting for the PS5" in log:
                    break
                if process.poll() is not None:
                    raise AssertionError(f"Host exited before startup ({process.returncode}):\n{log}")
                time.sleep(0.25)
            else:
                raise AssertionError(f"Host did not finish startup in 30 seconds:\n{log}")
            assert "PS5 WEBKIT AUTOLOADER" in log, log
            assert "[+]" in log, log
            assert "\x1b[" not in log, "ANSI escapes leaked into redirected output"
            assert "�" not in log, "Console text could not be decoded cleanly"
            print("Host startup and redirected console output verified")
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
