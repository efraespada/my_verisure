"""Small valid image fixtures generated locally, without private camera bytes.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import base64
from functools import cache
from io import BytesIO

from PIL import Image


@cache
def synthetic_jpeg_base64() -> str:
    """Return an encoded 2×2 JPEG rather than base64-encoded placeholder text."""
    with BytesIO() as stream, Image.new("RGB", (2, 2), color="black") as image:
        image.save(stream, format="JPEG")
        return base64.b64encode(stream.getvalue()).decode("ascii")
