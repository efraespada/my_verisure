"""Prevent local provider device identities from becoming CLI fixtures.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from pathlib import Path


def test_cli_fixtures_do_not_include_runtime_device_identities():
    """Keep account identifiers out of test filenames and their JSON contents."""
    if any(Path(__file__).parent.glob("my_verisure_device_*.json")):
        raise AssertionError("Runtime device identities must not be CLI fixtures")
