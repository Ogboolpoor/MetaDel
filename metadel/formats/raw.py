"""Camera RAW handler: CR2, CR3, NEF, ARW, DNG.

RAW metadata is the most persistent (MakerNotes carry the camera serial and lens
serial) and RAW files embed large, often *unedited* preview JPEGs. We strip all
metadata and every embedded preview, keeping the ICC profile.

Safety rule: if exiftool cannot write a particular RAW without risk, the wipe
raises and the pipeline leaves the original untouched — better to do nothing than
to corrupt an irreplaceable RAW.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.models import Family, Residual
from ..engine import exiftool
from .base import HandlerError, MetadataHandler
from .thumbnails import verify_no_thumbnails


class RawHandler(MetadataHandler):
    name = "raw"
    family = Family.RAW
    file_types = frozenset({"CR2", "CR3", "NEF", "ARW", "DNG"})
    requires_exiftool = True

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        res = exiftool.strip_all(path, keep_icc=keep_icc)
        if res.returncode != 0:
            msg = res.err_text.strip() or res.out_text.strip() or "unknown error"
            raise HandlerError(
                f"exiftool could not safely strip this RAW ({msg}); left untouched."
            )
        return [
            "EXIF/GPS",
            "XMP",
            "IPTC",
            "MakerNotes (camera/lens serials)",
            "Embedded previews (JpgFromRaw)",
            "Thumbnails",
        ]

    def native_verify(self, path: Path, tags: Optional[dict]) -> list[Residual]:
        return verify_no_thumbnails(tags)
