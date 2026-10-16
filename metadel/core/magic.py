"""Pure-Python magic-byte sniffing.

Used as a fallback type detector when exiftool is not available, and as a fast,
dependency-free gate. exiftool stays authoritative when present (it tells apart the
TIFF-based RAW subtypes that magic bytes cannot).
"""

from __future__ import annotations

import zipfile
from pathlib import Path


def _ftyp_brand(head: bytes) -> str:
    # ISO-BMFF: [size:4][b"ftyp":4][major_brand:4]...
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return head[8:12].decode("latin-1", "replace").strip()
    return ""


def _sniff_ooxml(path: Path) -> str:
    try:
        with zipfile.ZipFile(path, "r") as z:
            names = z.namelist()
    except (zipfile.BadZipFile, OSError):
        return ""
    if any(n.startswith("word/") for n in names):
        return "DOCX"
    if any(n.startswith("xl/") for n in names):
        return "XLSX"
    if any(n.startswith("ppt/") for n in names):
        return "PPTX"
    return ""


def sniff(path: Path) -> str:
    """Return an exiftool-style FileType string, or "" if unrecognised."""
    p = Path(path)
    try:
        with open(p, "rb") as fh:
            head = fh.read(32)
    except OSError:
        return ""

    if head[:3] == b"\xff\xd8\xff":
        return "JPEG"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "WEBP"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        if head[8:10] == b"CR":  # Canon CR2 marker inside the TIFF header
            return "CR2"
        return "TIFF"
    if head[:5] == b"%PDF-":
        return "PDF"
    if head[:4] == b"fLaC":
        return "FLAC"
    if head[:3] == b"ID3":
        return "MP3"
    if len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
        return "MP3"  # MPEG audio frame sync

    brand = _ftyp_brand(head)
    if brand:
        if brand == "crx":
            return "CR3"
        if brand == "qt":
            return "MOV"
        if brand.startswith(("hei", "hev", "mif", "msf")):
            return "HEIC"
        return "MP4"

    if head[:4] == b"PK\x03\x04":
        return _sniff_ooxml(p)
    return ""
