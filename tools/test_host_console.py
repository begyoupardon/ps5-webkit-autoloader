#!/usr/bin/env python3
"""Exercise the console code embedded in release hosts without a Windows PC."""

import ctypes
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest


RUNTIME = Path(__file__).with_name("host_console_runtime.py").read_text(encoding="utf-8")


class FakeOutput:
    def __init__(self, encoding, tty):
        self.encoding = encoding
        self.tty = tty
        self.lines = []

    def isatty(self):
        return self.tty

    def print(self, text, flush):
        assert flush
        text.encode(self.encoding)  # Simulate the real stream's strict encoding.
        self.lines.append(text)


class FakeKernel:
    def __init__(self, vt_supported):
        self.vt_supported = vt_supported
        self.mode_set = None

    def GetStdHandle(self, handle):
        assert handle == -11
        return 1

    def GetConsoleMode(self, handle, mode):
        mode._obj.value = 0x0001
        return 1

    def SetConsoleMode(self, handle, mode):
        self.mode_set = mode
        return int(self.vt_supported)


def run_runtime(os_name, output, kernel=None):
    namespace = {
        "COLOR": True,
        "os": SimpleNamespace(name=os_name),
        "sys": SimpleNamespace(stdout=output),
        "print": output.print,
    }
    with patch.object(ctypes, "windll", SimpleNamespace(kernel32=kernel), create=True):
        exec(RUNTIME, namespace)
    return namespace


class HostConsoleTest(unittest.TestCase):
    def test_modern_windows_console_enables_color_and_uses_ascii_border(self):
        output = FakeOutput("utf-8", True)
        kernel = FakeKernel(True)
        runtime = run_runtime("nt", output, kernel)
        runtime["say"]("┌─┐")
        self.assertTrue(runtime["COLOR"])
        self.assertEqual(kernel.mode_set, 0x0005)
        self.assertEqual(output.lines, ["+-+"])

    def test_legacy_console_disables_ansi_and_uses_ascii_border(self):
        output = FakeOutput("cp1252", True)
        runtime = run_runtime("nt", output, FakeKernel(False))
        runtime["say"]("┌─┐ Tardis")
        self.assertFalse(runtime["COLOR"])
        self.assertEqual(output.lines, ["+-+ Tardis"])

    def test_redirected_output_does_not_enable_ansi(self):
        output = FakeOutput("cp1252", False)
        runtime = run_runtime("nt", output)
        runtime["say"]("│  └─┘")
        self.assertFalse(runtime["COLOR"])
        self.assertEqual(output.lines, ["|  +-+"])

    def test_missing_windows_console_api_keeps_host_running(self):
        output = FakeOutput("cp1252", True)
        runtime = run_runtime("nt", output)
        runtime["say"]("└─┘")
        self.assertFalse(runtime["COLOR"])
        self.assertEqual(output.lines, ["+-+"])

    def test_other_platforms_keep_existing_color_behavior(self):
        output = FakeOutput("utf-8", True)
        runtime = run_runtime("posix", output)
        self.assertTrue(runtime["COLOR"])


if __name__ == "__main__":
    unittest.main()
