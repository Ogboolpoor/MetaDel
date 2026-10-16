"""MetaDel — fully local, offline metadata remover.

Hard rules (see README):
  1. Completely offline. No network calls, no telemetry, no auto-updates.
  2. Metadata lives in several containers at once (EXIF, XMP, IPTC, MakerNotes,
     thumbnails, document properties). Cleaning one is not cleaning the others.
  3. "Deleted" != "clean". A file is clean only after it is re-read and confirmed empty.
  4. Unknown format is never touched blindly — we say "can't" and leave it as is.
  5. The original is never damaged: we work on a copy and replace only after a
     successful verification.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
