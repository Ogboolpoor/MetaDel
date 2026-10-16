"""End-to-end photo round-trip through the real pipeline.

Skipped automatically when exiftool/ffmpeg are not installed, so the stdlib-only
suite still runs everywhere.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from metadel.core.models import OutputMode, Status
from metadel.core.pipeline import Pipeline
from metadel.core.process import run
from metadel.engine import exiftool
from metadel.engine.tools import (
    exiftool_available,
    exiftool_path,
    ffmpeg_available,
    ffmpeg_path,
)


@unittest.skipUnless(exiftool_available() and ffmpeg_available(), "needs exiftool + ffmpeg")
class TestPhotoPipeline(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.jpg = self.dir / "p.jpg"
        run([str(ffmpeg_path()), "-loglevel", "error", "-y", "-f", "lavfi",
             "-i", "color=c=red:s=32x32", "-frames:v", "1", str(self.jpg)])
        run([str(exiftool_path()), "-overwrite_original", "-q",
             "-Artist=Secret", "-Make=Cam", "-Copyright=c",
             "-GPSLatitude=50", "-GPSLatitudeRef=N",
             "-GPSLongitude=30", "-GPSLongitudeRef=E", str(self.jpg)])

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_starts_dirty(self):
        tags = exiftool.read_tags(self.jpg)
        self.assertIn("GPS:GPSLatitude", tags)
        self.assertTrue(any(k.endswith(":Artist") for k in tags))

    def test_clean_and_verify(self):
        res = Pipeline(output_mode=OutputMode.REPLACE).process(self.jpg)
        self.assertEqual(res.status, Status.CLEANED)
        tags = exiftool.read_tags(self.jpg)
        self.assertFalse(any(k.startswith("GPS:") for k in tags), "GPS survived")
        self.assertFalse(any(k.endswith(":Artist") for k in tags), "Artist survived")
        self.assertFalse(any(k.endswith(":Copyright") for k in tags), "Copyright survived")


if __name__ == "__main__":
    unittest.main()
