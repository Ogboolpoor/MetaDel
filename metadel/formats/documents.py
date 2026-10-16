"""Document handlers: PDF (pikepdf) and OOXML DOCX/XLSX/PPTX (zip surgery)."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional

from ..core.models import Family, Residual
from ..core.util import truncate
from .base import HandlerError, MetadataHandler

# --------------------------------------------------------------------------- PDF


class PdfHandler(MetadataHandler):
    name = "pdf"
    family = Family.DOCUMENT
    file_types = frozenset({"PDF"})
    requires_exiftool = False  # pikepdf does the wipe and a native re-read verifies it

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        try:
            import pikepdf
        except ImportError as exc:  # pragma: no cover - environment guard
            raise HandlerError("pikepdf is not installed (pip install pikepdf).") from exc

        with pikepdf.open(str(path), allow_overwriting_input=True) as pdf:
            # 1. Document Info dictionary: Author, Producer, Creator, Create/Mod dates,
            #    Title, Subject, Keywords, and any custom keys.
            try:
                del pdf.trailer.Info
            except (KeyError, AttributeError):
                pass
            # 2. XMP metadata stream attached to the document catalog.
            try:
                if pikepdf.Name.Metadata in pdf.Root:
                    del pdf.Root.Metadata
            except (KeyError, AttributeError):
                pass
            # 3. Full rewrite (not an incremental update) so the old objects are gone.
            pdf.save(str(path), linearize=False)

        return ["PDF Info dictionary (author/producer/dates/title)", "XMP metadata stream"]

    def native_verify(self, path: Path, tags: Optional[dict]) -> list[Residual]:
        try:
            import pikepdf
        except ImportError:  # pragma: no cover
            return []
        out: list[Residual] = []
        with pikepdf.open(str(path)) as pdf:
            info = pdf.trailer.get(pikepdf.Name.Info, None)
            if info is not None:
                for key in info.keys():
                    out.append(
                        Residual("PDF", str(key).lstrip("/"), truncate(str(info.get(key))))
                    )
            if pikepdf.Name.Metadata in pdf.Root:
                out.append(Residual("XMP", "Metadata", "stream present"))
        return out


# ------------------------------------------------------------------------- OOXML

_RELS = "_rels/.rels"
_CONTENT_TYPES = "[Content_Types].xml"
_DOCPROPS = "docProps/"

_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

_XML_DECL = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'


def _xml_bytes(root: ET.Element) -> bytes:
    return _XML_DECL + ET.tostring(root, encoding="unicode").encode("utf-8")


def _strip_rels(data: bytes) -> bytes:
    """Drop package relationships that point at docProps parts / the thumbnail."""
    ET.register_namespace("", _REL_NS)
    root = ET.fromstring(data)
    for rel in list(root):
        target = rel.get("Target", "").lstrip("/").lower()
        rtype = rel.get("Type", "").lower()
        if (
            target.startswith("docprops/")
            or "core-properties" in rtype
            or "extended-properties" in rtype
            or "custom-properties" in rtype
            or "thumbnail" in rtype
        ):
            root.remove(rel)
    return _xml_bytes(root)


def _strip_content_types(data: bytes) -> bytes:
    """Drop content-type overrides for the removed docProps parts."""
    ET.register_namespace("", _CT_NS)
    root = ET.fromstring(data)
    for override in list(root):
        if override.tag.endswith("}Override"):
            part = override.get("PartName", "").lower()
            if part.startswith("/docprops/"):
                root.remove(override)
    return _xml_bytes(root)


class OoxmlHandler(MetadataHandler):
    name = "ooxml"
    family = Family.DOCUMENT
    file_types = frozenset({"DOCX", "XLSX", "PPTX"})
    requires_exiftool = False  # zip surgery + native re-read; exiftool used only if present

    def wipe(self, path: Path, *, keep_icc: bool = True) -> list[str]:
        src = Path(path)
        tmp = src.with_name(src.name + ".metadel_zip.tmp")
        removed: list[str] = []
        try:
            with zipfile.ZipFile(src, "r") as zin:
                infos = {i.filename: i for i in zin.infolist()}
                with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
                    for name in zin.namelist():
                        if name.startswith(_DOCPROPS):
                            removed.append(name)
                            continue
                        data = zin.read(name)
                        if name == _RELS:
                            data = _strip_rels(data)
                        elif name == _CONTENT_TYPES:
                            data = _strip_content_types(data)
                        # New ZipInfo => per-entry timestamps reset to the neutral
                        # 1980-01-01 epoch, so the archive itself leaks no dates.
                        zi = zipfile.ZipInfo(name)
                        zi.compress_type = infos[name].compress_type
                        zi.external_attr = infos[name].external_attr
                        zout.writestr(zi, data)
        except (zipfile.BadZipFile, OSError) as exc:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise HandlerError(f"could not rewrite OOXML package: {exc}") from exc

        os.replace(tmp, src)
        if not removed:
            removed = ["(no docProps parts present)"]
        return [
            "docProps/core.xml (author, last-modified-by, dates, revision)",
            "docProps/app.xml (company, total editing time, template, app name)",
            "docProps/custom.xml",
            "docProps/thumbnail",
            "per-entry ZIP timestamps",
        ]

    def native_verify(self, path: Path, tags: Optional[dict]) -> list[Residual]:
        out: list[Residual] = []
        with zipfile.ZipFile(path, "r") as z:
            for name in z.namelist():
                if name.startswith(_DOCPROPS):
                    out.append(Residual("OOXML", name, "part still present"))
        return out
