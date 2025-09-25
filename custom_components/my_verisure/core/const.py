"""Constants for the My Verisure integration."""

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
DEFAULT_SCAN_INTERVAL = 10  # minutes

# Entity configuration
ENTITY_NAMES = {
    "alarm_control_panel": "My Verisure",
    "sensor_alarm_status": "General Alarm Status",
    "sensor_active_alarms": "Active Alarms",
    "sensor_panel_state": "Panel State",
    "sensor_last_updated": "Last Updated",
    "binary_sensor_internal_day": "Internal Day Alarm",
    "binary_sensor_internal_night": "Internal Night Alarm",
    "binary_sensor_internal_total": "Internal Total Alarm",
    "binary_sensor_external": "External Alarm",
}


# Device configuration
DEVICE_INFO = {
    "manufacturer": "Verisure",
    "model": "Alarm System",
    "sw_version": "1.0.0",
    "configuration_url": "https://github.com/efraespada/my_verisure",
}

# API endpoints
VERISURE_GRAPHQL_URL = "https://customers.securitasdirect.es/owa-api/graphql"
