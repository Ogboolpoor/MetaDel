"""Command-line interface — handy for batch use and for testing without the GUI.

    python -m metadel.cli env                 show tool availability
    python -m metadel.cli inspect FILE...     dump what metadata a file still has
    python -m metadel.cli clean [opts] FILE   wipe + verify files
        --copy         write *_clean.<ext> instead of replacing the original
        --strip-icc    also remove the ICC colour profile (default: keep it)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core.detector import detect
from .core.models import OutputMode, Status
from .core.pipeline import Pipeline
from .engine import exiftool
from .engine.tools import exiftool_available, ffmpeg_available

_MARK = {
    Status.CLEANED: "OK ",
    Status.UNSUPPORTED: "-- ",
    Status.FAILED_VERIFICATION: "!! ",
    Status.ERROR: "ERR",
}


def cmd_env(_args: argparse.Namespace) -> int:
    et = "found" if exiftool_available() else "MISSING"
    ff = "found" if ffmpeg_available() else "MISSING"
    print(f"exiftool: {et}")
    print(f"ffmpeg:   {ff}")
    if not exiftool_available():
        print("\nexiftool is required for photo/RAW/video. Put exiftool.exe in 'tools'.")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    for f in args.files:
        p = Path(f)
        det = detect(p)
        print(f"\n=== {p} ===")
        print(f"type: {det.label}  family: {det.family.value}  supported: {det.supported}")
        if exiftool_available():
            try:
                tags = exiftool.read_tags(p)
            except Exception as exc:
                print(f"  (exiftool read error: {exc})")
                continue
            for key, val in sorted(tags.items()):
                if key == "SourceFile":
                    continue
                print(f"  {key} = {val}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    pipeline = Pipeline(
        keep_icc=not args.strip_icc,
        output_mode=OutputMode.COPY if args.copy else OutputMode.REPLACE,
    )
    worst = 0
    for f in args.files:
        res = pipeline.process(Path(f))
        mark = _MARK.get(res.status, "???")
        print(f"[{mark}] {Path(f).name}  ({res.detected_label})")
        if res.status is Status.CLEANED:
            if res.output_path and res.output_path != Path(f):
                print(f"        -> {res.output_path.name}")
        elif res.status is Status.FAILED_VERIFICATION and res.report:
            print(f"        {res.report.residual_count} residual(s):")
            for r in res.report.residuals[:20]:
                print(f"          - {r}")
            worst = max(worst, 2)
        elif res.status is Status.ERROR:
            print(f"        {res.error}")
            worst = max(worst, 1)
    return worst


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metadel", description="Local, offline metadata remover.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("env", help="show tool availability").set_defaults(func=cmd_env)

    p_inspect = sub.add_parser("inspect", help="show remaining metadata")
    p_inspect.add_argument("files", nargs="+")
    p_inspect.set_defaults(func=cmd_inspect)

    p_clean = sub.add_parser("clean", help="wipe + verify")
    p_clean.add_argument("files", nargs="+")
    p_clean.add_argument("--copy", action="store_true", help="write *_clean copy, keep original")
    p_clean.add_argument("--strip-icc", action="store_true", help="also remove ICC colour profile")
    p_clean.set_defaults(func=cmd_clean)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
