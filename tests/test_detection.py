"""Magic-byte detection — pure stdlib, no exiftool / external deps needed."""

import os
import tempfile
import unittest
from pathlib import Path

from metadel.core import magic


class TestMagic(unittest.TestCase):
    def _write(self, data: bytes) -> Path:
        fd, name = tempfile.mkstemp()
        os.write(fd, data)
        os.close(fd)
        self.addCleanup(os.unlink, name)
        return Path(name)

    def test_jpeg(self):
        self.assertEqual(magic.sniff(self._write(b"\xff\xd8\xff\xe0" + b"0" * 20)), "JPEG")

    def test_png(self):
        self.assertEqual(magic.sniff(self._write(b"\x89PNG\r\n\x1a\n" + b"0" * 20)), "PNG")

    def test_pdf(self):
        self.assertEqual(magic.sniff(self._write(b"%PDF-1.7\n" + b"0" * 20)), "PDF")

    def test_flac(self):
        self.assertEqual(magic.sniff(self._write(b"fLaC" + b"0" * 20)), "FLAC")

    def test_id3_mp3(self):
        self.assertEqual(magic.sniff(self._write(b"ID3\x03\x00" + b"0" * 20)), "MP3")

    def test_webp(self):
        self.assertEqual(magic.sniff(self._write(b"RIFF\x00\x00\x00\x00WEBPVP8 ")), "WEBP")

    def test_mp4(self):
        self.assertEqual(magic.sniff(self._write(b"\x00\x00\x00\x18ftypisom" + b"0" * 12)), "MP4")

    def test_mov(self):
        self.assertEqual(magic.sniff(self._write(b"\x00\x00\x00\x14ftypqt  " + b"0" * 12)), "MOV")

    def test_heic(self):
        self.assertEqual(magic.sniff(self._write(b"\x00\x00\x00\x18ftypheic" + b"0" * 12)), "HEIC")

    def test_cr3(self):
        self.assertEqual(magic.sniff(self._write(b"\x00\x00\x00\x18ftypcrx " + b"0" * 12)), "CR3")

    def test_unknown(self):
        self.assertEqual(magic.sniff(self._write(b"just some random bytes here")), "")


if __name__ == "__main__":
    unittest.main()
