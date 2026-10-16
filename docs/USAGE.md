# MetaDel — usage and technical details

Local, offline removal of **all** metadata from files. No network, no telemetry, no
auto-update — no network calls at all. It removes every metadata container at once
(not just the popular fields) and **verifies itself**: a file counts as clean only
after a re-read confirms nothing is left.

## Hard rules

1. **Offline.** Nothing is ever sent anywhere. The only place external processes
   (exiftool/ffmpeg) are launched is `metadel/core/process.py` — easy to audit.
2. **Every container at once** — EXIF/GPS, IPTC, XMP, MakerNotes, Photoshop, document
   properties, and **embedded thumbnails/previews** as a deliberate separate step.
3. **Deleted != clean.** After wiping, the file is re-read; whatever survived is shown.
4. **Unknown formats are left untouched** — status "unsupported", file unchanged.
5. **The original is never damaged.** Work happens on a copy; the original is replaced
   only after a clean copy is verified (atomic).

## Supported formats

| Family | Formats | Engine |
|---|---|---|
| Photo | JPEG, PNG, WebP, TIFF, HEIC | exiftool |
| RAW | CR2, CR3, NEF, ARW, DNG | exiftool |
| Documents | PDF | pikepdf |
| Documents | DOCX, XLSX, PPTX | zipfile (package surgery) |
| Video | MP4, MOV | ffmpeg + exiftool |
| Audio | MP3, FLAC | mutagen |

## Run

Easiest: double-click **`MetaDel.exe`** in the project root (the `tools\` folder must
sit next to it). First launch takes 3–5 s while the single-file build unpacks. Rebuild
the exe with `./build_exe.ps1`.

The window UI is available in **Ukrainian and English** (switch with the Language
selector, top-right).

**Workflow:** add files (drag-and-drop or the buttons) → **Clean** (cleans + verifies
into staged copies; originals are not touched) → **Save selected** or **Save all**
(writes the cleaned files out). "Save as" chooses between replacing the original or
writing a `*_clean` copy.

From source:

```powershell
python -m metadel              # GUI
python run.py                  # same

# CLI (batch / scripting / tests):
python -m metadel.cli env                      # check the engine is present
python -m metadel.cli inspect "photo.jpg"      # show what metadata is inside
python -m metadel.cli clean "photo.jpg"        # clean (replaces the original)
python -m metadel.cli clean --copy *.jpg       # clean into *_clean.jpg copies
python -m metadel.cli clean --strip-icc x.jpg  # also drop the ICC colour profile
```

## Install (from source)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# then put tools\exiftool.exe and tools\ffmpeg.exe in place — see tools\README.txt
```

`exiftool` and `ffmpeg` are external executables, not pip packages. MetaDel looks for
them next to the app / in `tools\`, then on `PATH`, then via `METADEL_EXIFTOOL` /
`METADEL_FFMPEG`.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Detection and OOXML cleaning run on the pure standard library (no exiftool, no
third-party packages). Photo/RAW/video tests need `exiftool.exe`/`ffmpeg.exe`.

## Notes & limits (honest)

- **ICC colour profile** is kept by default (so colours don't shift); drop it with
  `--strip-icc` / the GUI checkbox.
- The verification allowlist (`metadel/formats/allowlist.py`) lists only *structural*
  fields; anything else counts as residue and fails verification. It is tuned against
  real stripped files.
- For TIFF-based files (TIFF/DNG/RAW) the IFD0-resident metadata tags are deleted by
  name, because a group wipe protects that image directory.
- Container dates in MP4/MOV can only be zeroed (`0000:00:00`), not deleted — a zeroed
  date leaks nothing and counts as clean.
- Video: data/telemetry tracks (e.g. GPS) are dropped; only A/V is kept.
- **Not yet validated on real camera RAW or HEIC** — handlers exist, samples needed.

## Layout

```
metadel/
  core/      models, process, detector, magic, verify, pipeline, logger, util
  engine/    tools (locate exiftool/ffmpeg), exiftool wrapper
  formats/   base, thumbnails, photo, raw, documents, media, registry, allowlist
  app/       main_window (PySide6 GUI, uk/en)
  cli.py     command line
tools/       exiftool.exe + ffmpeg.exe go here
tests/       unit tests
MetaDel.exe  single-file build (build_exe.ps1)
```
