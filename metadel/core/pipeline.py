"""The wipe pipeline, split into two phases so the UI can clean and save separately:

    prepare:  detect -> (unsupported? stop) -> copy -> wipe -> verify
              on success the cleaned file is left STAGED (a temp next to the original);
              the original is not touched.
    commit:   move the staged file to its final place (replace original / *_clean copy).
    discard:  drop the staged temp without saving.

    process = prepare + commit (one-shot, used by the CLI).

The original file is never modified until a staged, verified-clean copy is committed.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from ..engine.tools import exiftool_available
from ..formats.registry import get_handler
from .detector import detect
from .models import OutputMode, Status, WipeResult
from .verify import verify


def _safe_unlink(path: Optional[Path]) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


class Pipeline:
    def __init__(
        self,
        *,
        keep_icc: bool = True,
        output_mode: OutputMode = OutputMode.REPLACE,
        logger=None,
    ) -> None:
        self.keep_icc = keep_icc
        self.output_mode = output_mode
        self.logger = logger

    def _log(self, msg: str) -> None:
        if self.logger:
            self.logger.info(msg)

    # -- phase 1: clean into a staged temp ----------------------------------

    def prepare(self, path: Path) -> WipeResult:
        src = Path(path)
        if not src.is_file():
            return WipeResult(src, Status.ERROR, error="File does not exist.")

        det = detect(src)
        self._log(f"{src.name}: detected {det.label} ({det.family.value})")

        if not det.supported:
            return WipeResult(
                src, Status.UNSUPPORTED, det,
                error="Unknown or unsupported format — left untouched.",
            )

        handler = get_handler(det.file_type)
        assert handler is not None

        if handler.requires_exiftool and not exiftool_available():
            return WipeResult(
                src, Status.ERROR, det,
                error="exiftool is required for this format but was not found. "
                      "Put exiftool.exe in the 'tools' folder.",
            )

        try:
            work = self._make_copy(src)
        except OSError as exc:
            return WipeResult(src, Status.ERROR, det, error=f"could not create working copy: {exc}")

        try:
            removed = handler.wipe(work, keep_icc=self.keep_icc)
        except Exception as exc:
            _safe_unlink(work)
            return WipeResult(src, Status.ERROR, det, error=str(exc))

        report = verify(work, handler)
        if not report.is_clean:
            _safe_unlink(work)
            return WipeResult(
                src, Status.FAILED_VERIFICATION, det, removed=removed, report=report,
                error="Residual metadata remained — original left untouched.",
            )

        self._log(f"{src.name}: cleaned (staged, not yet saved)")
        return WipeResult(src, Status.CLEANED, det, removed=removed, report=report, staged_path=work)

    # -- phase 2: save / discard --------------------------------------------

    def commit(self, result: WipeResult, output_mode: Optional[OutputMode] = None) -> WipeResult:
        mode = output_mode or self.output_mode
        if result.status is not Status.CLEANED or result.staged_path is None:
            return result

        src = result.path
        dest = src if mode is OutputMode.REPLACE else self._clean_name(src)
        try:
            self._place(result.staged_path, dest)
        except OSError as exc:
            result.status = Status.ERROR
            result.error = f"verified clean but could not write output: {exc}"
            return result

        _safe_unlink(result.staged_path)  # one-shot: consume the staged copy
        result.staged_path = None
        result.output_path = dest
        self._log(f"{src.name}: saved -> {dest.name}")
        return result

    def commit_to(self, result: WipeResult, dest: Path) -> WipeResult:
        """Save the staged clean file to an explicit destination path.

        The staged copy is *copied* (not moved), so the same cleaned file can be
        saved again, any number of times, to different places.
        """
        if result.status is not Status.CLEANED or result.staged_path is None:
            return result
        result.error = ""
        dest = Path(dest)
        # The cleaned file keeps its original format, so it must keep the original
        # extension too — a name typed without one would leave an unopenable file.
        suffix = result.path.suffix
        if suffix and dest.suffix.lower() != suffix.lower():
            dest = dest.with_name(dest.name + suffix)
        try:
            self._place(result.staged_path, dest)
        except OSError as exc:
            result.error = f"could not save to {dest}: {exc}"
            return result
        result.output_path = dest  # last place it was saved (for the report)
        self._log(f"{result.path.name}: saved -> {dest}")
        return result

    def discard(self, result: WipeResult) -> None:
        _safe_unlink(result.staged_path)
        result.staged_path = None

    # -- one-shot (CLI) ------------------------------------------------------

    def process(self, path: Path) -> WipeResult:
        res = self.prepare(path)
        if res.status is Status.CLEANED:
            res = self.commit(res)
        return res

    # -- internals -----------------------------------------------------------

    def _make_copy(self, src: Path) -> Path:
        # Staged in the system temp dir (NOT next to the original), so cleaning never
        # drops a file into the user's folder; the extension is preserved so the
        # handlers' tools detect the format.
        fd, name = tempfile.mkstemp(prefix="metadel_", suffix=src.suffix or ".tmp")
        os.close(fd)
        work = Path(name)
        shutil.copyfile(src, work)
        return work

    @staticmethod
    def _place(work: Path, dest: Path) -> None:
        """Copy the staged file to dest atomically: write a temp in dest's own
        directory, then os.replace it into place. Cross-volume safe; never leaves a
        half-written destination."""
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".metadel_new")
        try:
            shutil.copyfile(work, tmp)
            os.replace(tmp, dest)
        except OSError:
            _safe_unlink(tmp)
            raise

    @staticmethod
    def _clean_name(src: Path) -> Path:
        out = src.with_name(f"{src.stem}_clean{src.suffix}")
        i = 1
        while out.exists():
            out = src.with_name(f"{src.stem}_clean_{i}{src.suffix}")
            i += 1
        return out
