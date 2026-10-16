# Rebuilds D:\Projects\MetaDel\MetaDel.exe (single file, no console window).
# Prereqs: .venv with requirements.txt installed + pyinstaller.
#   .\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
# Note: keep the tools\ folder (exiftool.exe / ffmpeg.exe) next to MetaDel.exe.

$root = $PSScriptRoot

# PyInstaller logs to stderr; Windows PowerShell 5.1 would treat that as a fatal
# error under "Stop", so check the exit code instead.
& "$root\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed `
    --name MetaDel `
    --distpath $root `
    --workpath "$root\build" `
    --specpath "$root\build" `
    "$root\run.py" 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

Write-Host "Done -> $root\MetaDel.exe   (tools\ must sit next to it)"
