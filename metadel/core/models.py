"""Data models shared across the whole pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Family(str, Enum):
    """Coarse format family — decides which handler is used."""

    PHOTO = "photo"
    RAW = "raw"
    DOCUMENT = "document"
    MEDIA = "media"
    UNKNOWN = "unknown"


class Status(str, Enum):
    """Final outcome for a single file."""

    CLEANED = "cleaned"                      # wiped AND verified empty
    UNSUPPORTED = "unsupported"              # unknown/unsupported -> left untouched
    FAILED_VERIFICATION = "failed_verification"  # wipe ran, but residue remained -> original kept
    ERROR = "error"                          # something broke -> original kept


class OutputMode(str, Enum):
    REPLACE = "replace"        # overwrite the original in place (after success)
    COPY = "copy"              # write a *_clean.<ext> next to the original, keep original


@dataclass(frozen=True)
class DetectedFormat:
    file_type: str            # exiftool FileType, e.g. "JPEG", "CR2", "DOCX"
    mime: str                 # exiftool MIMEType
    family: Family
    handler: str              # handler name that will process it
    supported: bool

    @property
    def label(self) -> str:
        return self.file_type or "?"


@dataclass
class Residual:
    """A single piece of metadata that survived the wipe."""

    group: str
    tag: str
    value: str = ""

    def __str__(self) -> str:
        v = f" = {self.value}" if self.value else ""
        return f"{self.group}:{self.tag}{v}"


@dataclass
class VerificationReport:
    is_clean: bool
    residuals: list[Residual] = field(default_factory=list)
    checked_with: list[str] = field(default_factory=list)  # e.g. ["native", "exiftool"]
    note: str = ""

    @property
    def residual_count(self) -> int:
        return len(self.residuals)


@dataclass
class WipeResult:
    path: Path
    status: Status
    detected: Optional[DetectedFormat] = None
    removed: list[str] = field(default_factory=list)   # human-readable containers touched
    report: Optional[VerificationReport] = None
    output_path: Optional[Path] = None                 # final saved location (after commit)
    staged_path: Optional[Path] = None                 # cleaned temp file awaiting save
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status is Status.CLEANED

    @property
    def detected_label(self) -> str:
        return self.detected.label if self.detected else "?"
