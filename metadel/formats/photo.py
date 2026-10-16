"""Raster photo handler: JPEG, PNG, WebP, TIFF, HEIC.

Removes every metadata container at once (EXIF/GPS, IPTC, XMP, MakerNotes,
Photoshop IRB) plus embedded thumbnails/previews, then leaves verification to the
pipeline. The ICC colour profile is preserved by default so colours don't shift.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.models import Family, Residual
from ..engine import exiftool
from .base import HandlerError, MetadataHandler
from .thumbnails import verify_no_thumbnails


class PhotoHandler(MetadataHandler):
    name = "photo"
    family = Family.PHOTO
    file_types = frozenset({"JPEG", "PNG", "WEBP", "TIFF", "HEIC", "HEIF"})
    requires_exiftool = True

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        res = exiftool.strip_all(path, keep_icc=keep_icc)
        if res.returncode != 0:
            msg = res.err_text.strip() or res.out_text.strip() or "unknown error"
            raise HandlerError(f"exiftool could not strip the file: {msg}")
        removed = ["EXIF/GPS", "IPTC", "XMP", "MakerNotes", "Photoshop", "Thumbnails/Previews"]
        if keep_icc:
            removed.append("(ICC colour profile preserved)")
        return removed

    def native_verify(self, path: Path, tags: Optional[dict]) -> list[Residual]:
        # Explicit thumbnail/preview check on top of the generic allowlist sweep.
        return verify_no_thumbnails(tags)
