"""Bounded JWT metadata inspection, never signature or identity verification.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import importlib
import logging
import math
import time
from typing import Any

jwt: Any = None
try:
    jwt = importlib.import_module("jwt")
except ImportError:
    pass

_LOGGER = logging.getLogger(__name__)
_MAX_TOKEN_BYTES = 64 * 1024


def is_jwt_expired(token: str, leeway: int = 30) -> bool:
    """Inspect expiry metadata, failing closed for invalid or unavailable decoding.

    ``leeway`` is a nonnegative early-refresh margin in seconds: expiry at 1000
    with margin 30 is considered expired from 970. This helper does not verify
    signatures, issuers, audiences, authentication or authorization.

    A decoded object without ``exp`` retains the legacy "no known JWT expiry"
    result. SessionManager separately enforces its maximum session age; callers
    must not use this result as proof that a credential is authentic or valid.
    """
    if type(leeway) is not int or leeway < 0:
        return True
    payload = get_jwt_payload(token)
    if payload is None:
        return True
    if "exp" not in payload:
        return False

    try:
        expiration = payload["exp"]
        current_time = time.time()
        if (
            type(expiration) not in (int, float)
            or not math.isfinite(expiration)
            or type(current_time) not in (int, float)
            or not math.isfinite(current_time)
        ):
            return True
        return current_time >= expiration - leeway
    except Exception:
        _LOGGER.debug("Unable to inspect JWT expiry metadata")
        return True


def get_jwt_payload(token: str) -> dict[str, Any] | None:
    """Return untrusted JSON object metadata from an ASCII JWT of at most 64 KiB.

    Signature and claim verification are deliberately disabled for metadata
    inspection. A new options dictionary is supplied for every call; mutations
    by the decoder cannot carry validation settings into another operation.
    The returned claims must never establish identity or grant authorization.
    """
    if (
        type(token) is not str
        or not 0 < len(token) <= _MAX_TOKEN_BYTES
        or not token.isascii()
    ):
        return None
    if jwt is None:
        _LOGGER.warning("PyJWT unavailable; JWT metadata cannot be inspected")
        return None
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        if type(payload) is not dict or any(type(key) is not str for key in payload):
            return None
        return payload
    except Exception:
        _LOGGER.debug("Unable to decode JWT metadata")
        return None
