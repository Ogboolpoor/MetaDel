"""Verification: prove a file is actually clean by re-reading it.

Two independent passes:
  * a format-native re-read (pikepdf / zip / mutagen) that needs no exiftool, and
  * a deep exiftool sweep that flags any surviving tag not on the structural allowlist.

A file is clean only when BOTH come back empty. If a format that needs exiftool
cannot be read by exiftool, we refuse to call it clean.
"""

from __future__ import annotations

from pathlib import Path

from ..engine import exiftool
from ..engine.tools import exiftool_available
from ..formats.allowlist import CONTAINER_DATE_TAGS, is_allowed, is_zero_date
from ..formats.base import MetadataHandler
from .models import Residual, VerificationReport
from .util import truncate


def _dedup(items: list[Residual]) -> list[Residual]:
    seen: set[tuple[str, str, str]] = set()
    out: list[Residual] = []
    for r in items:
        key = (r.group, r.tag, r.value)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def verify(path: Path, handler: MetadataHandler, *, use_exiftool: bool = True) -> VerificationReport:
    residuals: list[Residual] = []
    checked: list[str] = []
    tags: dict | None = None

    if use_exiftool and exiftool_available():
        try:
            tags = exiftool.read_tags(Path(path))
            checked.append("exiftool")
        except Exception as exc:
            residuals.append(Residual("engine", "exiftool_read_error", truncate(exc)))
            tags = None

    # Format-native residual check (works even without exiftool).
    try:
        native = handler.native_verify(Path(path), tags)
    except Exception as exc:
        native = [Residual("engine", f"{handler.name}_verify_error", truncate(exc))]
    if native:
        residuals.extend(native)
    checked.append("native")

    # Generic allowlist sweep over everything exiftool can still see.
    if tags is not None:
        for key, val in tags.items():
            if key == "SourceFile":
                continue
            group, _, tag = key.partition(":")
            tag = tag or group
            if is_allowed(tag):
                continue
            # Mandatory container dates can only be zeroed, not deleted; a zeroed
            # value leaks nothing. A real date here is still a residual.
            if tag in CONTAINER_DATE_TAGS and is_zero_date(val):
                continue
            # Unparsed per-track structural atoms (codec config like esds, sample
            # grouping, etc.) live in Track1/Track2/... groups and carry no user data.
            if tag.startswith("Unknown_") and group.startswith("Track"):
                continue
            residuals.append(Residual(group, tag, truncate(val)))

    residuals = _dedup(residuals)

    if handler.requires_exiftool and tags is None:
        return VerificationReport(
            False,
            residuals,
            checked,
            note="exiftool unavailable — cannot confirm this format is clean",
        )

    return VerificationReport(len(residuals) == 0, residuals, checked)
