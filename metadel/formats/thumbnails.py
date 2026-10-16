"""Embedded thumbnails / previews — handled as their own deliberate step.

Why this is separate: the classic leak is that you crop or redact the main image,
but an *unedited* original survives inside the file as an embedded thumbnail or
camera preview. So previews are cleared explicitly (see exiftool.THUMBNAIL_CLEAR_ARGS
applied during the wipe) and checked explicitly here, never left to chance.
"""

from __future__ import annotations

from typing import Optional

from ..core.models import Residual
from ..core.util import truncate

# Tag (short) names that represent an embedded image-of-the-image.
THUMBNAIL_RESIDUAL_TAGS: frozenset[str] = frozenset(
    {
        "ThumbnailImage",
        "ThumbnailTIFF",
        "ThumbnailOffset",
        "ThumbnailLength",
        "PreviewImage",
        "PreviewTIFF",
        "PreviewPICT",
        "OtherImage",
        "JpgFromRaw",
        "JpgFromRaw2",
        "PhotoshopThumbnail",
        "MPImage",
        "PreviewImageStart",
        "PreviewImageLength",
    }
)


def verify_no_thumbnails(tags: Optional[dict]) -> list[Residual]:
    """Return residuals for any embedded thumbnail/preview still present."""
    if not tags:
        return []
    found: list[Residual] = []
    for key, val in tags.items():
        group, _, tag = key.partition(":")
        tag = tag or group
        if tag in THUMBNAIL_RESIDUAL_TAGS:
            found.append(Residual(group, tag, truncate(val)))
    return found
