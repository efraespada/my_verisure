"""Constants for the My Verisure integration."""

from datetime import timedelta
import logging

DOMAIN = "my_verisure"

LOGGER = logging.getLogger(__package__)

# Configuration keys
CONF_USER = "user"
CONF_PASSWORD = "password"
CONF_INSTALLATION_ID = "installation_id"
CONF_PHONE_ID = "phone_id"
CONF_OTP_CODE = "otp_code"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = timedelta(minutes=3)

# API endpoints
VERISURE_GRAPHQL_URL = "https://customers.securitasdirect.es/owa-api/graphql"

# Platform names
PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor", "camera", "lock", "switch"] 