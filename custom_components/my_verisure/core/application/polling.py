"""Provider-safe polling interval policy shared by configuration and runtime.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from ..const import DEFAULT_SCAN_INTERVAL

MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 1440


def is_valid_scan_interval(value: object) -> bool:
    """Accept exact integer minutes, from one minute through one day."""
    return type(value) is int and MIN_SCAN_INTERVAL <= value <= MAX_SCAN_INTERVAL


def normalize_scan_interval(value: object) -> int:
    """Recover invalid saved options with the ten-minute polling default."""
    return (
        value
        if isinstance(value, int) and is_valid_scan_interval(value)
        else DEFAULT_SCAN_INTERVAL
    )
