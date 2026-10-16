"""Focused exiftool wrapper: detect, read-all (for verification), and strip-all."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..core.process import ProcResult, ProcessError, run
from .tools import exiftool_path

# Tags that must be cleared on top of ``-all=`` because they live in odd places
# (embedded previews / thumbnails are the classic survivors).
THUMBNAIL_CLEAR_ARGS = [
    "-ThumbnailImage=",
    "-ThumbnailTIFF=",
    "-PreviewImage=",
    "-PreviewTIFF=",
    "-PreviewPICT=",
    "-OtherImage=",
    "-JpgFromRaw=",
    "-JpgFromRaw2=",
    "-PhotoshopThumbnail=",
    "-MPImage=",
]

# Group-level deletes (-all=, -EXIF:all=) do NOT remove these from TIFF-based
# files (TIFF, DNG and many RAW): exiftool protects the IFD0 image directory, so
# metadata tags that live there survive a group wipe. We delete them by name.
# Harmless for JPEG/PNG (already gone via -all=); these are metadata-only names,
# so structural/colour/calibration tags are never touched. Anything missed here
# is still caught by the deny-by-default verifier.
IFD0_META_CLEAR_ARGS = [
    "-Artist=", "-Copyright=", "-Software=", "-ImageDescription=",
    "-ModifyDate=", "-Make=", "-Model=", "-HostComputer=",
    "-DocumentName=", "-PageName=", "-Rating=", "-RatingPercent=",
    "-ProcessingSoftware=", "-SerialNumber=", "-CameraSerialNumber=",
    "-LensSerialNumber=", "-InternalSerialNumber=", "-OwnerName=",
    "-UniqueCameraModel=", "-CameraLabel=",
    "-XPTitle=", "-XPComment=", "-XPAuthor=", "-XPKeywords=", "-XPSubject=",
    "-ImageHistory=", "-ImageUniqueID=", "-ImageNumber=",
    "-Creator=", "-By-line=", "-Headline=", "-Caption-Abstract=",
]


def _base() -> list[str]:
    return [str(exiftool_path())]


def detect_filetype(path: Path) -> tuple[str, str]:
    """Return (FileType, MIMEType) as exiftool sees them. Empty strings if unknown."""
    args = _base() + ["-json", "-FileType", "-MIMEType", "--", str(path)]
    res = run(args, timeout=60)
    try:
        data = json.loads(res.out_text or "[]")
    except json.JSONDecodeError:
        return "", ""
    if not data:
        return "", ""
    d = data[0]
    return d.get("FileType", "") or "", d.get("MIMEType", "") or ""


def read_tags(path: Path) -> dict:
    """Read *every* tag (incl. unknown/duplicate) grouped by family-1 group.

    Keys look like ``"GPS:GPSLatitude"`` / ``"MakerNotes:SerialNumber"``.
    Binary blobs come back as ``"(Binary data ... bytes)"`` rather than raw bytes.
    Used by the verifier to prove a file is actually empty.
    """
    args = _base() + ["-json", "-G1", "-a", "-u", "-s", "-e", "--", str(path)]
    res = run(args, timeout=180)
    if not res.stdout:
        raise ProcessError(f"exiftool read returned nothing: {res.err_text.strip()}")
    try:
        data = json.loads(res.out_text)
    except json.JSONDecodeError as exc:
        raise ProcessError(f"exiftool read produced invalid JSON: {exc}") from exc
    return data[0] if data else {}


def strip_all(path: Path, *, keep_icc: bool = True, extra: Optional[list[str]] = None) -> ProcResult:
    """Remove all metadata from ``path`` in place.

    ``keep_icc`` preserves the ICC colour profile (needed for correct colours) while
    removing everything identifying. Implemented with exiftool's documented
    "delete all, then copy ICC back from the original" recipe.
    """
    args = _base() + ["-all=", "-overwrite_original", "-m"]
    args += THUMBNAIL_CLEAR_ARGS
    args += IFD0_META_CLEAR_ARGS
    if keep_icc:
        args += ["-tagsfromfile", "@", "-icc_profile:all"]
    if extra:
        args += extra
    args += ["--", str(path)]
    return run(args, timeout=300)


def clear_tags(path: Path, tag_args: list[str], *, extra: Optional[list[str]] = None) -> ProcResult:
    """Clear a specific set of tags (e.g. container dates / GPS for video)."""
    args = _base() + ["-overwrite_original", "-m"] + tag_args
    if extra:
        args += extra
    args += ["--", str(path)]
    return run(args, timeout=180)
