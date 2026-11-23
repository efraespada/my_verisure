"""Bounded regression vectors for decoder-facing camera metadata.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from io import BytesIO
import random
from struct import pack
from unittest.mock import Mock
import zlib

from PIL import Image, TiffImagePlugin
import pytest

from custom_components.my_verisure.core import camera_image_sanitizer as sanitizer
from custom_components.my_verisure.core.file_manager import FileManager


def _image(image_format="JPEG", *, mode="RGB", progressive=False):
    with BytesIO() as output:
        with Image.new(mode, (2, 2)) as image:
            image.save(output, format=image_format, progressive=progressive)
        return output.getvalue()


def _jpeg_segment(marker, payload):
    return b"\xff" + bytes([marker]) + pack(">H", len(payload) + 2) + payload


def _png_chunk(kind, payload):
    return (
        pack(">I", len(payload))
        + kind
        + payload
        + pack(">I", zlib.crc32(kind + payload))
    )


def _save(files, contents):
    import base64

    return files.save_base64_image("camera.jpg", base64.b64encode(contents).decode())


@pytest.mark.parametrize(
    "mode,progressive", [("RGB", False), ("RGB", True), ("L", False), ("CMYK", False)]
)
def test_normal_jpeg_pixel_stream_is_unchanged(tmp_path, mode, progressive):
    contents = _image(mode=mode, progressive=progressive)
    files = FileManager(tmp_path)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == contents


def test_benign_exif_is_removed_without_changing_decoded_pixels(tmp_path):
    original = _image()
    exif = Image.Exif()
    exif[0x010E] = "Synthetic camera fixture"
    contents = original[:2] + _jpeg_segment(0xE1, exif.tobytes()) + original[2:]
    files = FileManager(tmp_path)

    assert _save(files, contents)

    stored = files.get_file_path("camera.jpg").read_bytes()
    assert stored == original
    with Image.open(BytesIO(contents)) as before, Image.open(BytesIO(stored)) as after:
        assert before.tobytes() == after.tobytes()
        assert not after.getexif()


def test_metadata_between_progressive_scans_is_removed(tmp_path):
    original = _image(progressive=True)
    first_scan = original.index(b"\xff\xda")
    next_table = original.index(b"\xff\xc4", first_scan + 2)
    contents = (
        original[:next_table]
        + _jpeg_segment(0xE1, b"Exif\0\0unused metadata")
        + original[next_table:]
    )
    files = FileManager(tmp_path)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == original


def test_entropy_byte_stuffing_does_not_count_as_header_segments(tmp_path, monkeypatch):
    with BytesIO() as output:
        with Image.frombytes(
            "RGB", (128, 128), random.Random(0).randbytes(128 * 128 * 3)
        ) as image:
            image.save(output, format="JPEG", quality=95)
        contents = output.getvalue()
    assert contents.count(b"\xff\x00") > 20
    monkeypatch.setattr(sanitizer, "_MAX_CONTAINER_PARTS", 20)
    files = FileManager(tmp_path)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == contents


@pytest.mark.parametrize("mode", ["RGBA", "P"])
def test_png_palette_and_transparency_pixels_are_preserved(tmp_path, mode):
    with BytesIO() as output:
        with Image.new(mode, (2, 2)) as image:
            if mode == "P":
                image.putpalette([255, 0, 0, 0, 255, 0] + [0] * 762)
                image.putdata([0, 1, 1, 0])
                image.save(output, format="PNG", transparency=0)
            else:
                image.putdata([(12, 34, 56, 78)] * 4)
                image.save(output, format="PNG")
        contents = output.getvalue()
    files = FileManager(tmp_path)

    assert _save(files, contents)

    stored = files.get_file_path("camera.jpg").read_bytes()
    assert stored == contents
    with Image.open(BytesIO(contents)) as before, Image.open(BytesIO(stored)) as after:
        assert before.convert("RGBA").tobytes() == after.convert("RGBA").tobytes()


def test_overlapping_exif_values_never_reach_the_tiff_parser(tmp_path, monkeypatch):
    # 64 overlapping entries cost <50 KiB if mistakenly parsed: no OOM vector.
    entries = 64
    size = 8 + 2 + 12 * entries + 4
    metadata = (
        b"Exif\0\0II"
        + pack("<HIH", 42, 8, entries)
        + b"".join(
            pack("<HHII", 1000 + index, 1, size - 1, 1) for index in range(entries)
        )
        + pack("<I", 0)
    )
    original = _image()
    contents = original[:2] + _jpeg_segment(0xE1, metadata) + original[2:]
    files = FileManager(tmp_path)
    parser = Mock(side_effect=AssertionError("EXIF parser must remain unreachable"))
    monkeypatch.setattr(TiffImagePlugin.ImageFileDirectory_v2, "load", parser)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == original
    parser.assert_not_called()


@pytest.mark.parametrize(
    "marker,payload",
    [
        (0xE1, b"Exif\0\0ignored"),
        (0xE2, b"MPF\0ignored"),
        (0xED, b"Photoshop 3.0\0ignored"),
        (0xFE, b"ignored comment"),
    ],
)
def test_unused_jpeg_metadata_is_removed_before_decoding(tmp_path, marker, payload):
    original = _image()
    contents = original[:2] + _jpeg_segment(marker, payload) + original[2:]
    files = FileManager(tmp_path)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == original


@pytest.mark.parametrize("kind", [b"eXIf", b"iCCP", b"zTXt", b"iTXt", b"tEXt"])
def test_unused_png_chunks_are_removed_without_decompression(tmp_path, kind):
    original = _image("PNG")
    # These metadata bodies need not be parseable by EXIF, ICC or text parsers.
    contents = original[:33] + _png_chunk(kind, b"unused metadata") + original[33:]
    files = FileManager(tmp_path)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == original


@pytest.mark.parametrize("kind", [b"acTL", b"fcTL", b"fdAT"])
def test_apng_control_chunks_are_rejected_before_open(tmp_path, monkeypatch, kind):
    original = _image("PNG")
    contents = original[:33] + _png_chunk(kind, b"unused control") + original[33:]
    files = FileManager(tmp_path)
    decoder = Mock(side_effect=AssertionError("APNG must not reach the decoder"))
    monkeypatch.setattr(Image, "open", decoder)

    assert not _save(files, contents)
    decoder.assert_not_called()


@pytest.mark.parametrize("image_format", ["TIFF", "GIF", "BMP"])
def test_unneeded_format_parsers_are_never_called(tmp_path, monkeypatch, image_format):
    contents = _image(image_format)
    files = FileManager(tmp_path)
    decoder = Mock(side_effect=AssertionError("unneeded parser must be unreachable"))
    monkeypatch.setattr(Image, "open", decoder)

    assert not _save(files, contents)
    decoder.assert_not_called()


def test_declared_png_dimensions_are_checked_before_open(tmp_path, monkeypatch):
    original = _image("PNG")
    contents = (
        original[:8]
        + _png_chunk(b"IHDR", pack(">IIBBBBB", 10000, 10000, 8, 2, 0, 0, 0))
        + original[33:]
    )
    files = FileManager(tmp_path)
    decoder = Mock(side_effect=AssertionError("dimension check must precede decoder"))
    monkeypatch.setattr(Image, "open", decoder)

    assert not _save(files, contents)
    decoder.assert_not_called()


def test_both_pillow_opens_use_only_jpeg_and_png(tmp_path, monkeypatch):
    contents = _image()
    files = FileManager(tmp_path)
    decoder = Mock(wraps=Image.open)
    monkeypatch.setattr(Image, "open", decoder)

    assert _save(files, contents)
    assert decoder.call_count == 2
    assert all(
        call.kwargs["formats"] == ["JPEG", "PNG"] for call in decoder.call_args_list
    )


@pytest.mark.parametrize(
    "contents",
    [b"\xff\xd8\xff\xe1\xff\xffx", b"\xff\xd8\xff\xd9", b"\x89PNG\r\n\x1a\n"],
)
def test_invalid_container_framing_is_rejected(contents):
    with pytest.raises(ValueError):
        sanitizer.sanitize_camera_image(contents, max_pixels=16_000_000)


def test_container_part_count_is_bounded(tmp_path, monkeypatch):
    files = FileManager(tmp_path)
    contents = _image()
    monkeypatch.setattr(sanitizer, "_MAX_CONTAINER_PARTS", 2)

    assert not _save(files, contents)


def _invalid_jpeg_cases():
    frame = _jpeg_segment(0xC0, b"\x08\x00\x02\x00\x02\x01")
    scan = _jpeg_segment(0xDA, b"\x01")
    return [
        pytest.param(b"\xff\xd8", id="empty-container"),
        pytest.param(b"\xff\xd8\x00", id="nonmarker-header-byte"),
        pytest.param(b"\xff\xd8\xff", id="unterminated-marker-fill"),
        pytest.param(b"\xff\xd8\xff\xe0\x00", id="partial-segment-length"),
        pytest.param(b"\xff\xd8\xff\xe0\x00\x01", id="segment-length-below-two"),
        pytest.param(b"\xff\xd8" + scan, id="scan-before-frame"),
        pytest.param(
            b"\xff\xd8" + frame + scan + b"pixels", id="entropy-without-end-marker"
        ),
        pytest.param(b"\xff\xd8" + frame + b"\xff\xd9", id="frame-without-scan"),
        pytest.param(
            b"\xff\xd8" + _jpeg_segment(0xC0, b"\x08\x00"), id="short-frame-header"
        ),
        pytest.param(
            b"\xff\xd8" + _jpeg_segment(0xC3, b"\x08\x00\x02\x00\x02\x01"),
            id="unsupported-lossless-frame",
        ),
        *[
            pytest.param(
                b"\xff\xd8\xff" + bytes([marker]), id=f"unexpected-marker-{marker:02x}"
            )
            for marker in (0, 1, 0xD8, 0xD0)
        ],
    ]


@pytest.mark.parametrize("contents", _invalid_jpeg_cases())
def test_invalid_jpeg_framing_never_reaches_pillow(tmp_path, monkeypatch, contents):
    files = FileManager(tmp_path)
    decoder = Mock(side_effect=AssertionError("framing must precede the decoder"))
    monkeypatch.setattr(Image, "open", decoder)

    assert not _save(files, contents)
    assert not files.get_file_path("camera.jpg").exists()
    decoder.assert_not_called()


def _invalid_png_cases():
    signature = b"\x89PNG\r\n\x1a\n"
    header = _png_chunk(b"IHDR", pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
    pixels = _png_chunk(b"IDAT", zlib.compress(b"\x00" + b"\x00" * 6))
    ending = _png_chunk(b"IEND", b"")
    corrupt_header = header[:-1] + bytes([header[-1] ^ 1])
    return [
        pytest.param(
            signature + pack(">I", 100) + header[4:], id="chunk-exceeds-container"
        ),
        pytest.param(signature + corrupt_header + pixels + ending, id="invalid-crc"),
        pytest.param(signature + ending, id="missing-header"),
        pytest.param(
            signature + _png_chunk(b"IHDR", b"short header"), id="short-header"
        ),
        pytest.param(
            signature + header + header + pixels + ending, id="duplicate-header"
        ),
        pytest.param(signature + header + _png_chunk(b"PLTE", b""), id="empty-palette"),
        pytest.param(
            signature + header + _png_chunk(b"PLTE", b"a" * 769), id="oversized-palette"
        ),
        pytest.param(
            signature + header + _png_chunk(b"PLTE", b"1234"),
            id="partial-palette-entry",
        ),
        pytest.param(
            signature + header + pixels + _png_chunk(b"PLTE", b"123") + ending,
            id="late-palette",
        ),
        pytest.param(
            signature + header + _png_chunk(b"tRNS", b""), id="empty-transparency"
        ),
        pytest.param(
            signature + header + _png_chunk(b"tRNS", b"a" * 257),
            id="oversized-transparency",
        ),
        pytest.param(
            signature + header + pixels + _png_chunk(b"tRNS", b"x") + ending,
            id="late-transparency",
        ),
        pytest.param(signature + header + ending, id="no-image-data"),
        pytest.param(
            signature + header + pixels + _png_chunk(b"IEND", b"x"),
            id="ending-has-payload",
        ),
        pytest.param(
            signature + header + pixels + ending + b"trailing", id="trailing-bytes"
        ),
        pytest.param(
            signature + header + _png_chunk(b"ABCD", b""), id="unknown-critical-chunk"
        ),
    ]


@pytest.mark.parametrize("contents", _invalid_png_cases())
def test_invalid_png_framing_never_reaches_pillow(tmp_path, monkeypatch, contents):
    files = FileManager(tmp_path)
    decoder = Mock(side_effect=AssertionError("framing must precede the decoder"))
    monkeypatch.setattr(Image, "open", decoder)

    assert not _save(files, contents)
    assert not files.get_file_path("camera.jpg").exists()
    decoder.assert_not_called()


def test_png_chunk_count_limit_is_enforced_before_pillow(tmp_path, monkeypatch):
    contents = _image("PNG")
    files = FileManager(tmp_path)
    decoder = Mock(side_effect=AssertionError("chunk budget must precede the decoder"))
    monkeypatch.setattr(Image, "open", decoder)
    monkeypatch.setattr(sanitizer, "_MAX_CONTAINER_PARTS", 1)

    assert not _save(files, contents)
    decoder.assert_not_called()


def test_valid_restart_markers_and_fill_bytes_keep_original_jpeg(tmp_path):
    with BytesIO() as output:
        with Image.frombytes(
            "RGB", (32, 32), random.Random(1).randbytes(32 * 32 * 3)
        ) as image:
            image.save(output, format="JPEG", restart_marker_blocks=1)
        original = output.getvalue()
    assert any(bytes([0xFF, marker]) in original for marker in range(0xD0, 0xD8))
    contents = original[:2] + b"\xff" + original[2:]
    files = FileManager(tmp_path)

    assert _save(files, contents)
    assert files.get_file_path("camera.jpg").read_bytes() == contents
