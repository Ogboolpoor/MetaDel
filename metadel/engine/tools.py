"""Locate the bundled command-line tools.

Search order for each tool:
  1. Explicit env override (METADEL_EXIFTOOL / METADEL_FFMPEG)
  2. Bundled ``tools/`` folder next to the project
  3. System PATH

Everything runs locally; these tools never need the network.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

# Where the bundled tools/ folder lives. When frozen by PyInstaller, look next to
# the .exe; otherwise look at the project root (parents[2] of this file).
if getattr(sys, "frozen", False):
    _APP_DIR = Path(sys.executable).resolve().parent
else:
    _APP_DIR = Path(__file__).resolve().parents[2]
_BUNDLED = _APP_DIR / "tools"


class ToolNotFound(RuntimeError):
    pass


def _locate(base: str, env_var: str) -> Optional[Path]:
    env = os.environ.get(env_var)
    if env:
        p = Path(env)
        if p.is_file():
            return p

    for name in (f"{base}.exe", base):
        cand = _BUNDLED / name
        if cand.is_file():
            return cand

    found = shutil.which(base)
    if found:
        return Path(found)
    return None


def exiftool_path() -> Path:
    p = _locate("exiftool", "METADEL_EXIFTOOL")
    if p is None:
        raise ToolNotFound(
            "exiftool not found. Put exiftool.exe in the 'tools' folder next to the "
            "app, set METADEL_EXIFTOOL, or add it to PATH."
        )
    return p


def ffmpeg_path() -> Path:
    p = _locate("ffmpeg", "METADEL_FFMPEG")
    if p is None:
        raise ToolNotFound(
            "ffmpeg not found. Put ffmpeg.exe in the 'tools' folder next to the "
            "app, set METADEL_FFMPEG, or add it to PATH."
        )
    return p


def exiftool_available() -> bool:
    try:
        exiftool_path()
        return True
    except ToolNotFound:
        return False


def ffmpeg_available() -> bool:
    try:
        ffmpeg_path()
        return True
    except ToolNotFound:
        return False
