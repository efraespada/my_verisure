"""Synthetic encrypted round trips for observed Web Push header forms.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import base64
import json
import os

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from firebase_messaging import FcmPushClient
from http_ece import encrypt

from decoder import decode


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def main():
    """Verify real encrypted round trips without provider or household data."""
    client_key = ec.generate_private_key(ec.SECP256R1())
    server_key = ec.generate_private_key(ec.SECP256R1())
    client_public = client_key.public_key().public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    server_public = server_key.public_key().public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    secret, salt = os.urandom(16), os.urandom(16)
    credentials = {
        "keys": {
            "private": b64(
                client_key.private_bytes(
                    Encoding.DER, PrivateFormat.PKCS8, NoEncryption()
                )
            ),
            "secret": b64(secret),
        }
    }
    expected = {"data": {"text": "synthetic photo-ready event"}}
    encrypted = encrypt(
        json.dumps(expected).encode(),
        salt=salt,
        private_key=server_key,
        dh=client_public,
        auth_secret=secret,
        version="aesgcm",
    )
    forms = [
        (
            f"p256ecdsa={b64(client_public)};dh={b64(server_public)}",
            f"salt={b64(salt)}",
        ),
        (
            f"dh={b64(server_public)};p256ecdsa={b64(client_public)}",
            f"salt={b64(salt)};rs=4096",
        ),
        (
            f' p256ecdsa="{b64(client_public)}" ; dh="{b64(server_public)}" ',
            f' salt="{b64(salt)}" ',
        ),
        (
            f"dh={base64.urlsafe_b64encode(server_public).decode()}",
            f"salt={base64.urlsafe_b64encode(salt).decode()}",
        ),
    ]
    for crypto, encryption in forms:
        record = {
            "envelope": {
                "raw_data": base64.b64encode(encrypted).decode(),
                "app_data": [
                    {"key": "crypto-key", "value": crypto},
                    {"key": "encryption", "value": encryption},
                ],
            }
        }
        assert decode(record, credentials) == expected
    legacy_failed = False
    try:
        FcmPushClient._decrypt_raw_data(
            credentials, forms[0][0][3:], forms[0][1][5:], encrypted
        )
    except (ValueError, TypeError):
        legacy_failed = True
    assert legacy_failed
    print(json.dumps({
        "round_trip_cases_passed": len(forms),
        "legacy_failure_reproduced": legacy_failed,
    }))


if __name__ == "__main__":
    main()
