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
DEFAULT_SCAN_INTERVAL = 10  # minutes

# Entity configuration
ENTITY_NAMES = {
    "alarm_control_panel": "My Verisure Alarm",
    "sensor_alarm_status": "General Alarm Status",
    "sensor_active_alarms": "Active Alarms",
    "sensor_panel_state": "Panel State",
    "sensor_last_updated": "Last Updated",
    "binary_sensor_internal_day": "Internal Day Alarm",
    "binary_sensor_internal_night": "Internal Night Alarm",
    "binary_sensor_internal_total": "Internal Total Alarm",
    "binary_sensor_external": "External Alarm",
}

# Import custom alarm names configuration
try:
    from .alarm_names_config import CUSTOM_ALARM_NAMES, CUSTOM_ALARM_DESCRIPTIONS
    ALARM_MODE_NAMES = CUSTOM_ALARM_NAMES
    ALARM_MODE_DESCRIPTIONS = CUSTOM_ALARM_DESCRIPTIONS
except ImportError:
    # Fallback to default names if config file doesn't exist
    ALARM_MODE_NAMES = {
        "armed_home": "En Casa",         # Valor por defecto de Home Assistant
        "armed_away": "Ausente",         # Valor por defecto de Home Assistant
        "armed_night": "Noche",          # Valor por defecto de Home Assistant
        "disarmed": "Desarmada",         # Valor por defecto de Home Assistant
    }
    
    ALARM_MODE_DESCRIPTIONS = {
        "armed_home": "Activa solo la alarma perimetral (externa)",
        "armed_away": "Activa todas las alarmas (total)",
        "armed_night": "Activa la alarma nocturna (interna noche)",
        "disarmed": "Desactiva todas las alarmas",
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
