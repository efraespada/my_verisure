"""Bound camera containers before opening them with an image decoder.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import zlib

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MAX_CONTAINER_PARTS = 4096
_JPEG_FRAMES = frozenset({0xC0, 0xC1, 0xC2})
_JPEG_OTHER_FRAMES = frozenset(
    {0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)


def sanitize_camera_image(contents: bytes, *, max_pixels: int) -> bytes:
    """Keep static JPEG/PNG pixels while removing decoder-facing metadata.

    EXIF, colour profiles and animation controls are not required by these
    snapshots. Some decoder versions process them before their pixel limits.
    This framing pass never decompresses data or follows metadata offsets.
    """
    if contents.startswith(b"\xff\xd8"):
        return _jpeg(contents, max_pixels)
    if contents.startswith(_PNG_SIGNATURE):
        return _png(contents, max_pixels)
    raise ValueError("unsupported camera image container")


def _check_geometry(width: int, height: int, max_pixels: int) -> None:
    if width <= 0 or height <= 0 or width * height > max_pixels:
        raise ValueError("camera image dimensions exceed limit")


def _jpeg(contents: bytes, max_pixels: int) -> bytes:
    output = bytearray(contents[:2])
    position = 2
    parts = 0
    scan_start: int | None = None
    has_frame = False
    has_scan = False
    while position < len(contents):
        if scan_start is not None:
            marker_start = contents.find(b"\xff", position)
            if marker_start < 0:
                break
            position = marker_start
        else:
            marker_start = position
        if contents[position] != 0xFF:
            raise ValueError("invalid JPEG marker")
        while position < len(contents) and contents[position] == 0xFF:
            position += 1
        if position >= len(contents):
            break
        marker = contents[position]
        position += 1
        if scan_start is not None:
            if marker == 0 or 0xD0 <= marker <= 0xD7:
                continue
            output.extend(contents[scan_start:marker_start])
            scan_start = None
        parts += 1
        if parts > _MAX_CONTAINER_PARTS:
            raise ValueError("too many camera image segments")
        if marker == 0xD9:
            if not has_frame or not has_scan or position != len(contents):
                raise ValueError("invalid JPEG ending")
            output.extend(b"\xff\xd9")
            return bytes(output)
        if marker in {0, 1, 0xD8} or 0xD0 <= marker <= 0xD7:
            raise ValueError("unexpected JPEG marker")
        if position + 2 > len(contents):
            break
        length = int.from_bytes(contents[position : position + 2], "big")
        end = position + length
        if length < 2 or end > len(contents):
            raise ValueError("invalid JPEG segment length")
        payload = contents[position + 2 : end]
        if marker in _JPEG_FRAMES:
            if len(payload) < 6:
                raise ValueError("invalid JPEG frame")
            _check_geometry(
                int.from_bytes(payload[3:5], "big"),
                int.from_bytes(payload[1:3], "big"),
                max_pixels,
            )
            has_frame = True
        elif marker in _JPEG_OTHER_FRAMES:
            raise ValueError("unsupported JPEG frame")
        metadata = 0xE0 <= marker <= 0xEF or marker == 0xFE
        safe_metadata = (
            marker == 0xE0 and len(payload) >= 14 and payload.startswith(b"JFIF\0")
        ) or (marker == 0xEE and len(payload) >= 12 and payload.startswith(b"Adobe"))
        if not metadata or safe_metadata:
            output.extend(contents[marker_start:end])
        position = end
        if marker == 0xDA:
            if not has_frame:
                raise ValueError("JPEG scan precedes frame")
            has_scan = True
            scan_start = position
    raise ValueError("truncated JPEG container")


def _png(contents: bytes, max_pixels: int) -> bytes:
    output = bytearray(_PNG_SIGNATURE)
    position = len(_PNG_SIGNATURE)
    has_header = False
    has_pixels = False
    for _ in range(_MAX_CONTAINER_PARTS):
        if position + 12 > len(contents):
            break
        length = int.from_bytes(contents[position : position + 4], "big")
        kind = contents[position + 4 : position + 8]
        end = position + 12 + length
        if end > len(contents):
            raise ValueError("invalid PNG chunk length")
        payload = contents[position + 8 : end - 4]
        crc = int.from_bytes(contents[end - 4 : end], "big")
        if zlib.crc32(memoryview(contents)[position + 4 : end - 4]) != crc:
            raise ValueError("invalid PNG chunk checksum")
        if not has_header and kind != b"IHDR":
            raise ValueError("PNG header required")
        if kind in {b"acTL", b"fcTL", b"fdAT"}:
            raise ValueError("animated camera image is unsupported")
        if kind == b"IHDR":
            if has_header or length != 13:
                raise ValueError("invalid PNG header")
            _check_geometry(
                int.from_bytes(payload[:4], "big"),
                int.from_bytes(payload[4:8], "big"),
                max_pixels,
            )
            has_header = True
        elif kind == b"PLTE":
            if has_pixels or not 0 < length <= 768 or length % 3:
                raise ValueError("invalid PNG palette")
        elif kind == b"tRNS":
            if has_pixels or not 0 < length <= 256:
                raise ValueError("invalid PNG transparency")
        elif kind == b"IDAT":
            has_pixels = True
        elif kind == b"IEND":
            if not has_pixels or length or end != len(contents):
                raise ValueError("invalid PNG ending")
            output.extend(contents[position:end])
            return bytes(output)
        elif not (kind[0] & 0x20):
            raise ValueError("unsupported PNG critical chunk")
        if kind in {b"IHDR", b"PLTE", b"tRNS", b"IDAT"}:
            output.extend(contents[position:end])
        position = end
    raise ValueError("truncated or oversized PNG container")
