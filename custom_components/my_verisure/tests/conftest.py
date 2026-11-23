"""Keep both HA harness versions inside per-test writable configuration.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import pytest


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Prevent the official harness's shared path from writing into the checkout."""
    return hass_tmp_config_dir
