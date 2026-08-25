"""Provider-independent OTP code validation."""

from __future__ import annotations

import re


OTP_CODE_PATTERN = re.compile(r"^[0-9]{6}$")


def is_valid_otp_code(value: object) -> bool:
    """Return whether an OTP code has the required exact format."""
    return isinstance(value, str) and OTP_CODE_PATTERN.fullmatch(value) is not None
