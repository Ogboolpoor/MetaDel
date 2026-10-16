"""Base class shared by every format handler."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..core.models import Family, Residual


class HandlerError(RuntimeError):
    """A handler could not complete the wipe (file is left untouched upstream)."""


class MetadataHandler:
    name: str = "base"
    family: Family = Family.UNKNOWN
    file_types: frozenset[str] = frozenset()
    # If True, a missing exiftool means we cannot safely confirm cleanliness,
    # so the pipeline refuses to process these formats rather than guess.
    requires_exiftool: bool = True

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        """Strip metadata from ``path`` (already a working copy) in place.

        Returns a human-readable list of containers that were targeted.
        Raises HandlerError if the wipe could not be performed.
        """
        raise NotImplementedError

    def native_verify(self, path: Path, tags: Optional[dict]) -> list[Residual]:
        """Format-native residual check that does not rely on exiftool.

        ``tags`` is the exiftool read (or None if exiftool is unavailable); handlers
        may reuse it or re-open the file with their own library.
        """
        return []
