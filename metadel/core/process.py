"""Thin, safe wrapper around external processes (exiftool / ffmpeg).

No shell, explicit timeout, no console window flashes on Windows. This is the only
place that spawns subprocesses, which keeps the offline guarantee auditable.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Sequence

# Hide the console window that would otherwise flash for each call on Windows.
_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class ProcessError(RuntimeError):
    """Raised when a process cannot be started or times out."""


@dataclass
class ProcResult:
    returncode: int
    stdout: bytes
    stderr: bytes

    @property
    def out_text(self) -> str:
        return self.stdout.decode("utf-8", errors="replace")

    @property
    def err_text(self) -> str:
        return self.stderr.decode("utf-8", errors="replace")

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run(
    cmd: Sequence[str],
    *,
    timeout: float = 120.0,
    input_bytes: Optional[bytes] = None,
) -> ProcResult:
    """Run ``cmd`` (a list of args, never a shell string) and capture output."""
    try:
        cp = subprocess.run(
            list(cmd),
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            creationflags=_CREATE_NO_WINDOW,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise ProcessError(f"Executable not found: {cmd[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProcessError(f"Timed out after {timeout:g}s: {cmd[0]}") from exc
    return ProcResult(cp.returncode, cp.stdout or b"", cp.stderr or b"")
