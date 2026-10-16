"""Format detection. exiftool is authoritative; magic bytes are the fallback.

If the type is not one we explicitly support, we report it unsupported so the
pipeline leaves the file untouched — we never guess at an unknown format.
"""

from __future__ import annotations

from pathlib import Path

from ..engine import exiftool
from ..engine.tools import exiftool_available
from ..formats.registry import canonical_type, get_handler
from . import magic
from .models import DetectedFormat, Family


def detect(path: Path) -> DetectedFormat:
    p = Path(path)
    file_type, mime = "", ""

    if exiftool_available():
        try:
            file_type, mime = exiftool.detect_filetype(p)
        except Exception:
            file_type, mime = "", ""

    if not file_type:
        file_type = magic.sniff(p)

    file_type = canonical_type(file_type)
    handler = get_handler(file_type)
    if handler is None:
        return DetectedFormat(file_type, mime, Family.UNKNOWN, "", supported=False)

    return DetectedFormat(file_type, mime, handler.family, handler.name, supported=True)
