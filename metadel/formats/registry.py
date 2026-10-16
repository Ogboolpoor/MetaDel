"""Maps a detected file type to the handler that knows how to clean it."""

from __future__ import annotations

from typing import Optional

from ..core.models import Family
from .base import MetadataHandler
from .documents import OoxmlHandler, PdfHandler
from .media import AudioHandler, VideoHandler
from .photo import PhotoHandler
from .raw import RawHandler

_HANDLERS: list[MetadataHandler] = [
    PhotoHandler(),
    RawHandler(),
    PdfHandler(),
    OoxmlHandler(),
    VideoHandler(),
    AudioHandler(),
]

_BY_TYPE: dict[str, MetadataHandler] = {}
for _h in _HANDLERS:
    for _ft in _h.file_types:
        _BY_TYPE[_ft.upper()] = _h


# exiftool sometimes reports a variant FileType (e.g. "Extended WEBP"); fold those
# onto the canonical type our handlers register.
_ALIASES: dict[str, str] = {"EXTENDED WEBP": "WEBP"}


def canonical_type(file_type: str) -> str:
    if not file_type:
        return ""
    upper = file_type.upper()
    if "WEBP" in upper:
        return "WEBP"
    return _ALIASES.get(upper, file_type)


def get_handler(file_type: str) -> Optional[MetadataHandler]:
    if not file_type:
        return None
    return _BY_TYPE.get(canonical_type(file_type).upper())


def family_of(file_type: str) -> Family:
    handler = get_handler(file_type)
    return handler.family if handler else Family.UNKNOWN


def supported_types() -> list[str]:
    return sorted(_BY_TYPE)
