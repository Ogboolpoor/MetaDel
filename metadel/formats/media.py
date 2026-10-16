"""Media handlers: MP4/MOV video (ffmpeg + exiftool) and MP3/FLAC audio (mutagen)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ..core.models import Family, Residual
from ..core.process import run
from .base import HandlerError, MetadataHandler


def _tail(text: str, lines: int = 3) -> str:
    parts = [p for p in text.strip().splitlines() if p.strip()]
    return " | ".join(parts[-lines:]) if parts else ""


# --------------------------------------------------------------------------- video


class VideoHandler(MetadataHandler):
    name = "video"
    family = Family.MEDIA
    file_types = frozenset({"MP4", "MOV"})
    requires_exiftool = True  # exiftool clears container dates and verifies

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        from ..engine import exiftool
        from ..engine.tools import ToolNotFound, ffmpeg_path

        try:
            ff = ffmpeg_path()
        except ToolNotFound as exc:
            raise HandlerError(str(exc)) from exc

        src = Path(path)
        tmp = src.with_name(src.name + ".metadel_ff" + src.suffix)

        # Re-mux without re-encoding: drop all format/stream metadata and chapters,
        # and drop data/telemetry tracks (e.g. GPS streams) by keeping only A/V.
        cmd = [
            str(ff), "-y", "-i", str(src),
            "-map", "0:v?", "-map", "0:a?",
            "-map_metadata", "-1", "-map_chapters", "-1",
            "-c", "copy", "-movflags", "+faststart",
            str(tmp),
        ]
        res = run(cmd, timeout=600)
        if res.returncode != 0 or not tmp.exists():
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise HandlerError(f"ffmpeg failed: {_tail(res.err_text)}")
        os.replace(tmp, src)

        # ffmpeg leaves the container header dates (mvhd/tkhd/mdhd) intact — clear
        # them and any stray atoms with exiftool. Verification will catch leftovers.
        exiftool.clear_tags(
            src,
            [
                "-ItemList:all=", "-Keys:all=", "-UserData:all=",
                "-XMP:all=", "-EXIF:all=", "-GPS:all=",
                "-QuickTime:Make=", "-QuickTime:Model=", "-QuickTime:Software=",
                "-QuickTime:GPSCoordinates=", "-QuickTime:CreationDate=",
                "-CreateDate=", "-ModifyDate=",
                "-TrackCreateDate=", "-TrackModifyDate=",
                "-MediaCreateDate=", "-MediaModifyDate=",
            ],
            extra=["-api", "QuickTimeUTC=1"],
        )

        return [
            "All stream/format tags (ffmpeg -map_metadata -1)",
            "Chapters",
            "Data/telemetry tracks (e.g. GPS)",
            "Container dates (create/modify)",
            "GPS / Make / Model / Software atoms",
            "XMP / EXIF atoms",
        ]


# --------------------------------------------------------------------------- audio


class AudioHandler(MetadataHandler):
    name = "audio"
    family = Family.MEDIA
    file_types = frozenset({"MP3", "FLAC"})
    requires_exiftool = False  # mutagen wipes and re-reads natively

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        try:
            import mutagen
            from mutagen.apev2 import APENoHeaderError, APEv2
            from mutagen.flac import FLAC
            from mutagen.id3 import ID3, ID3NoHeaderError
        except ImportError as exc:  # pragma: no cover - environment guard
            raise HandlerError("mutagen is not installed (pip install mutagen).") from exc

        removed: list[str] = []
        f = mutagen.File(str(path))

        if isinstance(f, FLAC):
            if f.tags:
                removed.append("Vorbis comments")
            if f.pictures:
                removed.append("Embedded pictures")
            f.delete()
            f.clear_pictures()
            f.save()
        else:
            # MP3 / MPEG: strip ID3 (v1 + v2) and any APE tags.
            try:
                ID3(str(path)).delete(str(path))  # delete_v1 and delete_v2 default True
                removed.append("ID3 tags (v1/v2) + embedded art")
            except ID3NoHeaderError:
                pass
            try:
                APEv2(str(path)).delete()
                removed.append("APE tags")
            except APENoHeaderError:
                pass

        if not removed:
            removed = ["(no tags present)"]
        return removed

    def native_verify(self, path: Path, tags: Optional[dict]) -> list[Residual]:
        import mutagen

        out: list[Residual] = []
        f = mutagen.File(str(path))
        if f is None:
            return out
        if getattr(f, "tags", None):
            try:
                keys = list(f.tags.keys())
            except (AttributeError, TypeError):
                keys = ["present"]
            for key in keys:
                out.append(Residual("AudioTag", str(key), "present"))
        pics = getattr(f, "pictures", None)
        if pics:
            out.append(Residual("Audio", "Picture", f"{len(pics)} embedded"))
        return out
