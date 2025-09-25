"""Constants and field names for My Verisure API."""

# API Endpoints
VERISURE_GRAPHQL_URL = "https://customers.securitasdirect.es/owa-api/graphql"

# GraphQL Query Names
LOGIN_MUTATION = "mkLoginToken"
VALIDATE_DEVICE_MUTATION = "mkValidateDevice"
SEND_OTP_MUTATION = "mkSendOTP"
CHECK_ALARM_QUERY = "CheckAlarm"
ARM_PANEL_MUTATION = "xSArmPanel"
ARM_STATUS_QUERY = "xSArmStatus"
DISARM_PANEL_MUTATION = "xSDisarmPanel"
DISARM_STATUS_QUERY = "xSDisarmStatus"
CHECK_ALARM_STATUS_QUERY = "xSCheckAlarmStatus"
INSTALLATIONS_QUERY = "mkInstallationList"
INSTALLATION_SERVICES_QUERY = "Srv"

# GraphQL Field Names
FIELD_RES = "res"
FIELD_MSG = "msg"
FIELD_HASH = "hash"
FIELD_STATUS = "status"
FIELD_REFERENCE_ID = "referenceId"
FIELD_REFRESH_TOKEN = "refreshToken"
FIELD_LANG = "lang"
FIELD_LEGALS = "legals"
FIELD_CHANGE_PASSWORD = "changePassword"
FIELD_NEED_DEVICE_AUTHORIZATION = "needDeviceAuthorization"
FIELD_PROTOM_RESPONSE = "protomResponse"
FIELD_PROTOM_RESPONSE_DATE = "protomResponseDate"
FIELD_NUMINST = "numinst"
FIELD_REQUEST_ID = "requestId"
FIELD_FORCED_ARMED = "forcedArmed"

# Error Fields
FIELD_ERROR = "error"
FIELD_ERROR_CODE = "code"
FIELD_ERROR_TYPE = "type"
FIELD_ERROR_ALLOW_FORCING = "allowForcing"
FIELD_ERROR_EXCEPTIONS_NUMBER = "exceptionsNumber"
FIELD_ERROR_SUID = "suid"

# Smartlock Fields
FIELD_SMARTLOCK_STATUS = "smartlockStatus"
FIELD_SMARTLOCK_STATE = "state"
FIELD_SMARTLOCK_DEVICE_ID = "deviceId"
FIELD_SMARTLOCK_UPDATED_ON_ARM = "updatedOnArm"

# Device Fields
FIELD_ID_DEVICE = "idDevice"
FIELD_ID_DEVICE_INDIGITALL = "idDeviceIndigitall"
FIELD_DEVICE_TYPE = "deviceType"
FIELD_DEVICE_VERSION = "deviceVersion"
FIELD_DEVICE_RESOLUTION = "deviceResolution"
FIELD_DEVICE_NAME = "deviceName"
FIELD_DEVICE_BRAND = "deviceBrand"
FIELD_DEVICE_OS_VERSION = "deviceOsVersion"
FIELD_UUID = "uuid"

# Installation Fields
FIELD_INSTALLATIONS = "installations"
FIELD_ALIAS = "alias"
FIELD_PANEL = "panel"
FIELD_TYPE = "type"
FIELD_NAME = "name"
FIELD_SURNAME = "surname"
FIELD_ADDRESS = "address"
FIELD_CITY = "city"
FIELD_POSTCODE = "postcode"
FIELD_PROVINCE = "province"
FIELD_EMAIL = "email"
FIELD_PHONE = "phone"
FIELD_DUE = "due"
FIELD_ROLE = "role"

# Service Fields
FIELD_SERVICES = "services"
FIELD_ID_SERVICE = "idService"
FIELD_ACTIVE = "active"
FIELD_VISIBLE = "visible"
FIELD_BDE = "bde"
FIELD_IS_PREMIUM = "isPremium"
FIELD_COD_OPER = "codOper"
FIELD_REQUEST = "request"
FIELD_MIN_WRAPPER_VERSION = "minWrapperVersion"
FIELD_UNPROTECT_ACTIVE = "unprotectActive"
FIELD_UNPROTECT_DEVICE_STATUS = "unprotectDeviceStatus"
FIELD_INST_DATE = "instDate"
FIELD_GENERIC_CONFIG = "genericConfig"
FIELD_TOTAL = "total"
FIELD_ATTRIBUTES = "attributes"
FIELD_ATTRIBUTE_NAME = "name"
FIELD_ATTRIBUTE_VALUE = "value"
FIELD_ATTRIBUTE_ACTIVE = "active"

# Configuration Fields
FIELD_CONFIG_REPO_USER = "configRepoUser"
FIELD_ALARM_PARTITIONS = "alarmPartitions"
FIELD_ENTER_STATES = "enterStates"
FIELD_LEAVE_STATES = "leaveStates"
FIELD_CAPABILITIES = "capabilities"
FIELD_LANGUAGE = "language"

# OTP Fields
FIELD_RECORD_ID = "recordId"
FIELD_OTP_HASH = "otpHash"
FIELD_AUTH_PHONES = "auth-phones"
FIELD_AUTH_OTP_HASH = "auth-otp-hash"
FIELD_AUTH_CODE = "auth-code"
FIELD_AUTH_TYPE = "auth-type"
FIELD_PHONE_ID = "id"
FIELD_PHONE_NUMBER = "phone"

# Request Fields
FIELD_REQUEST_ARM = "request"
FIELD_CURRENT_STATUS = "currentStatus"
FIELD_FORCE_ARMING_REMOTE_ID = "forceArmingRemoteId"
FIELD_ARM_AND_LOCK = "armAndLock"
FIELD_COUNTER = "counter"

# Response Status Values
RESPONSE_OK = "OK"
RESPONSE_KO = "KO"
RESPONSE_WAIT = "WAIT"

# Error Codes
ERROR_INVALID_CREDENTIALS = "60091"
ERROR_OTP_REQUIRED = "10001"
ERROR_UNAUTHORIZED = "10010"

# Device Default Values
DEFAULT_DEVICE_VERSION = "10.154.0"
DEFAULT_CALLBY = "OWI_10"
DEFAULT_COUNTRY = "ES"
DEFAULT_LANG = "es"

# Session Fields
FIELD_LOGIN_TIMESTAMP = "loginTimestamp"
FIELD_USER = "user"
FIELD_ID = "id"
FIELD_COUNTRY = "country"
FIELD_CALLBY = "callby"

# Header Names
HEADER_APP = "App"
HEADER_EXTENSION = "Extension"
HEADER_AUTH = "auth"
HEADER_SECURITY = "Security"
HEADER_NUMINST = "numinst"
HEADER_PANEL = "panel"
HEADER_X_CAPABILITIES = "x-capabilities"

# Header Values
HEADER_APP_VALUE = '{"origin": "native", "appVersion": "10.154.0"}'
HEADER_EXTENSION_VALUE = '{"mode": "full"}'

# Cache Fields
FIELD_CACHE_SIZE = "cache_size"
FIELD_TTL_SECONDS = "ttl_seconds"
FIELD_CACHED_INSTALLATIONS = "cached_installations"
FIELD_CACHE_TIMESTAMPS = "cache_timestamps"
FIELD_TIMESTAMP = "timestamp"
FIELD_AGE_SECONDS = "age_seconds"
FIELD_IS_VALID = "is_valid"

# Alarm Status Fields
FIELD_INTERNAL = "internal"
FIELD_EXTERNAL = "external"
FIELD_DAY = "day"
FIELD_NIGHT = "night"
FIELD_TOTAL = "total"
FIELD_ALARM = "alarm"
FIELD_ALARM_STATUS = "status"

# Session File Fields
FIELD_COOKIES = "cookies"
FIELD_SESSION_DATA = "session_data"
FIELD_DEVICE_IDENTIFIERS = "device_identifiers"
FIELD_SAVED_TIME = "saved_time"
FIELD_GENERATED_TIME = "generated_time"
