"""Allowlist of *structural* tags for verification.

The verifier reads every tag that survived the wipe. Anything whose (short) tag
name is NOT in this set is treated as residual metadata and fails verification.

This is deliberately conservative: structural/intrinsic fields (image geometry,
codec parameters, filesystem facts) are allowed; anything that could carry
identity, history, location, device, or authorship is not — even when it shares a
container with structural data (e.g. PNG text chunks, TIFF IFD0, QuickTime atoms).

NOTE: this list is tuned against real stripped files. When a genuinely structural
tag is wrongly flagged, add it here; never add a tag that can carry user info.
"""

from __future__ import annotations

ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        # --- exiftool / filesystem bookkeeping (not embedded in the file) ---
        "ExifToolVersion",
        "FileName",
        "Directory",
        "FileSize",
        "FileModifyDate",
        "FileAccessDate",
        "FileCreateDate",
        "FileInodeChangeDate",
        "FilePermissions",
        "FileType",
        "FileTypeExtension",
        "MIMEType",
        "ExifByteOrder",
        "Warning",  # exiftool's own minor-warning line; not file metadata
        # --- generic raster geometry / encoding ---
        "ImageWidth",
        "ImageHeight",
        "ImageSize",
        "Megapixels",
        "BitDepth",
        "BitsPerSample",
        "ColorComponents",
        "ColorType",
        "Compression",
        "EncodingProcess",
        "YCbCrSubSampling",
        "PhotometricInterpretation",
        "SamplesPerPixel",
        "RowsPerStrip",
        "StripOffsets",
        "StripByteCounts",
        "PlanarConfiguration",
        "FillOrder",
        # --- TIFF/IFD0 structural (these stay; metadata in IFD0 is deleted by name) ---
        "NewSubfileType",
        "SubfileType",
        "Thresholding",
        "CellWidth",
        "CellLength",
        "Orientation",
        "Predictor",
        "WhitePoint",
        "PrimaryChromaticities",
        "YCbCrCoefficients",
        "YCbCrPositioning",
        "ReferenceBlackWhite",
        "TileWidth",
        "TileLength",
        "TileOffsets",
        "TileByteCounts",
        "SampleFormat",
        "SMinSampleValue",
        "SMaxSampleValue",
        "ExtraSamples",
        "ColorMap",
        "TransferFunction",
        "Indexed",
        "JPEGTables",
        # --- DPI / resolution (not identifying) ---
        "XResolution",
        "YResolution",
        "ResolutionUnit",
        "JFIFVersion",
        # --- PNG structural / colour chunks ---
        "Filter",
        "Interlace",
        "Gamma",
        "SignificantBits",
        "BackgroundColor",
        "Palette",
        "Transparency",
        "PixelsPerUnitX",
        "PixelsPerUnitY",
        "PixelUnits",
        "WhitePointX",
        "WhitePointY",
        "RedX",
        "RedY",
        "GreenX",
        "GreenY",
        "BlueX",
        "BlueY",
        "SRGBRendering",
        # --- WebP structural ---
        "VP8Version",
        "HorizontalScale",
        "VerticalScale",
        "AlphaIsUsed",
        # --- ISO-BMFF / HEIC / MP4 / MOV structural container ---
        "MajorBrand",
        "MinorVersion",
        "CompatibleBrands",
        "HandlerType",
        "HandlerVendorID",
        "HandlerClass",
        "HandlerDescription",  # usually generic ("SoundHandler"/"VideoHandler")
        "PrimaryItemReference",
        "MovieHeaderVersion",
        "TimeScale",
        "MediaTimeScale",
        "Duration",
        "MediaDuration",
        "TrackDuration",
        "PreferredRate",
        "PreferredVolume",
        "PreviewTime",
        "PreviewDuration",
        "PosterTime",
        "SelectionTime",
        "SelectionDuration",
        "CurrentTime",
        "NextTrackID",
        "TrackHeaderVersion",
        "TrackID",
        "TrackLayer",
        "TrackVolume",
        "MatrixStructure",
        "GraphicsMode",
        "OpColor",
        "CompressorID",
        "CompressorName",
        "SourceImageWidth",
        "SourceImageHeight",
        "PixelAspectRatio",
        "CleanApertureWidth",
        "CleanApertureHeight",
        "ProductionApertureWidth",
        "ProductionApertureHeight",
        "EncodedPixelsDimensions",
        "MediaHeaderVersion",
        "MediaLanguageCode",
        "VideoFrameRate",
        "FrameRate",
        "FrameCount",
        "MovieDataSize",
        "MovieDataOffset",
        "MediaDataSize",
        "MediaDataOffset",
        "ColorRepresentation",
        "ColorProfiles",
        "VideoFullRangeFlag",
        "MatrixCoefficients",
        "ColorPrimaries",
        "TransferCharacteristics",
        "BitDepthLuma",
        "BitDepthChroma",
        # --- audio structural (MP3 / FLAC) ---
        "MPEGAudioVersion",
        "AudioLayer",
        "AudioBitrate",
        "SampleRate",
        "AudioSampleRate",
        "ChannelMode",
        "Channels",
        "AudioChannels",
        "AudioFormat",
        "AudioBitsPerSample",
        "Emphasis",
        "MSStereo",
        "IntensityStereo",
        "TotalSamples",
        "Balance",
        "MaxBitrate",
        "AvgBitrate",
        "BufferSize",
        "Encoding",
        "AvgBytesPerSec",
        # FLAC writes a "vendor" string on save (the tool name, e.g. libFLAC/mutagen);
        # it is not user-identifying and cannot be removed without a low-level rewrite.
        "Vendor",
        "VendorID",
        # --- ZIP container structure (OOXML is a zip; these describe the archive,
        #     not the document; per-entry dates are reset to the neutral 1980 epoch) ---
        "ZipRequiredVersion",
        "ZipBitFlag",
        "ZipCompression",
        "ZipModifyDate",
        "ZipCRC",
        "ZipCompressedSize",
        "ZipUncompressedSize",
        "ZipFileName",
        # --- PDF structure (author/history is removed by pikepdf; these only
        #     describe the document structure) ---
        "PDFVersion",
        "Linearized",
        "PageCount",
        "Encryption",
        "Tagged",
        # --- MPEG audio frame-header bits (part of the stream, not tags) ---
        "CopyrightFlag",
        "OriginalMedia",
        "VBRScale",
        # --- FLAC STREAMINFO (intrinsic stream parameters / empty padding) ---
        "BlockSizeMin",
        "BlockSizeMax",
        "FrameSizeMin",
        "FrameSizeMax",
        "MD5Signature",
        "Padding",
        # --- MP4 / MOV structural boxes and sample tables ---
        "Free",
        "MediaData",
        "AVCConfiguration",
        "HEVCConfiguration",
        "AV1Configuration",
        "ChunkOffset",
        "ChunkOffset64",
        "CompositionTimeToSample",
        "SampleSizes",
        "SampleToChunk",
        "SyncSampleTable",
        "TimeToSampleTable",
        "SampleDescription",
        "DataReference",
        "AverageBitrate",
        "Unknown_edts",
        "SampleGroupDescription",
        "SampleToGroup",
        "SampleDependency",
    }
)

# Container date tags that live in mandatory boxes (mvhd/tkhd/mdhd) and cannot be
# deleted — only zeroed. A zeroed value ("0000:00:00 00:00:00") leaks nothing and
# counts as clean; any real date here is still treated as residual.
CONTAINER_DATE_TAGS: frozenset[str] = frozenset(
    {
        "CreateDate",
        "ModifyDate",
        "TrackCreateDate",
        "TrackModifyDate",
        "MediaCreateDate",
        "MediaModifyDate",
    }
)


def is_zero_date(value: object) -> bool:
    s = str(value).strip()
    return s == "" or s.startswith("0000:00:00") or s.startswith("0000-00-00")


def is_allowed(tag: str) -> bool:
    return tag in ALLOWED_TAGS
