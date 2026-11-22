"""Experimental offline decoder for observed legacy Web Push envelopes.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import base64
import json

from cryptography.hazmat.primitives.serialization import load_der_private_key
from http_ece import decrypt


def b64(value):
    """Decode padded or unpadded base64url header/key material."""
    value = value.encode("ascii")
    return base64.urlsafe_b64decode(value + b"=" * (-len(value) % 4))


def parameters(header):
    """Extract named parameters from the observed single header value."""
    return {
        key.strip(): value.strip().strip('"')
        for chunk in header.split(";")
        for key, separator, value in [chunk.partition("=")]
        if separator
    }


def decode(record, credentials):
    """Decrypt one observed aesgcm envelope with its receiver credentials."""
    envelope = record["envelope"]
    data = {item["key"]: item["value"] for item in envelope["app_data"]}
    crypto = parameters(data["crypto-key"])
    encryption = parameters(data["encryption"])
    raw = decrypt(
        base64.b64decode(envelope["raw_data"]),
        salt=b64(encryption["salt"]),
        dh=b64(crypto["dh"]),
        private_key=load_der_private_key(
            b64(credentials["keys"]["private"]), password=None
        ),
        auth_secret=b64(credentials["keys"]["secret"]),
        version="aesgcm",
    )
    return json.loads(raw)
