"""OOXML wipe — pure stdlib (zipfile), no exiftool needed.

Builds a minimal DOCX with author/company/revision metadata, wipes it, and
proves the docProps parts and their package references are gone.
"""

import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from metadel.core.detector import detect
from metadel.core.models import Family, Status
from metadel.core.pipeline import Pipeline
from metadel.formats.documents import OoxmlHandler

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:creator>Secret Author</dc:creator><cp:lastModifiedBy>Secret Editor</cp:lastModifiedBy><cp:revision>7</cp:revision>
</cp:coreProperties>"""

APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
<Company>Secret Corp</Company><TotalTime>123</TotalTime></Properties>"""

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>"""


def make_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/document.xml", DOCUMENT)
        z.writestr("docProps/core.xml", CORE)
        z.writestr("docProps/app.xml", APP)


class TestOoxml(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.docx = self.dir / "sample.docx"
        make_docx(self.docx)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_detect_as_docx(self):
        det = detect(self.docx)
        self.assertEqual(det.file_type, "DOCX")
        self.assertEqual(det.family, Family.DOCUMENT)
        self.assertTrue(det.supported)

    def test_wipe_removes_docprops_and_refs(self):
        OoxmlHandler().wipe(self.docx)
        with zipfile.ZipFile(self.docx) as z:
            names = z.namelist()
            self.assertNotIn("docProps/core.xml", names)
            self.assertNotIn("docProps/app.xml", names)
            self.assertIn("word/document.xml", names)  # real content survives
            self.assertNotIn("docProps/", z.read("_rels/.rels").decode("utf-8"))
            self.assertNotIn("/docProps/", z.read("[Content_Types].xml").decode("utf-8"))

    def test_native_verify_is_clean(self):
        OoxmlHandler().wipe(self.docx)
        self.assertEqual(OoxmlHandler().native_verify(self.docx, None), [])

    def test_save_keeps_extension(self):
        pipe = Pipeline()
        res = pipe.prepare(self.docx)
        self.assertEqual(res.status, Status.CLEANED, res.error)
        res = pipe.commit_to(res, self.dir / "renamed")  # typed without ".docx"
        self.assertEqual(res.output_path, self.dir / "renamed.docx")
        self.assertTrue((self.dir / "renamed.docx").is_file())
        self.assertFalse((self.dir / "renamed").exists())
        pipe.discard(res)


if __name__ == "__main__":
    unittest.main()
