MetaDel bundled tools
=====================

Put two Windows executables here so MetaDel can work fully offline:

  tools\exiftool.exe   (required for photo / RAW / video, and for verification)
  tools\ffmpeg.exe     (required for MP4 / MOV)

How MetaDel finds them (in order):
  1. Environment variables METADEL_EXIFTOOL / METADEL_FFMPEG (full path to .exe)
  2. This tools\ folder
  3. System PATH

Where to get them (download once, on any machine; they run locally, no network):
  exiftool : https://exiftool.org/   -> download the Windows EXE, rename it from
             "exiftool(-k).exe" to "exiftool.exe", drop it here.
  ffmpeg   : https://www.gyan.dev/ffmpeg/builds/  (or ffmpeg.org) -> copy ffmpeg.exe here.

Nothing in MetaDel ever contacts the internet at run time.
