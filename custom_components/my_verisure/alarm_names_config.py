"""
Configuration file for customizing alarm mode names.
Supports multiple languages based on Home Assistant configuration.
"""

# Multi-language alarm mode names
ALARM_NAMES_BY_LANGUAGE = {
    "es": {  # Spanish
        "armed_home": "Perimetral",
        "armed_away": "Total",
        "armed_night": "Noche",
        "disarmed": "Desarmada",
    },
    "en": {  # English
        "armed_home": "Home",
        "armed_away": "Away",
        "armed_night": "Night",
        "disarmed": "Disarmed",
    },
    "ca": {  # Catalan
        "armed_home": "Perimetral",
        "armed_away": "Total",
        "armed_night": "Nit",
        "disarmed": "Desarmada",
    },
    "eu": {  # Basque
        "armed_home": "Perimetrala",
        "armed_away": "Guztia",
        "armed_night": "Gaua",
        "disarmed": "Desarmatua",
    },
    "gl": {  # Galician
        "armed_home": "Perimetral",
        "armed_away": "Total",
        "armed_night": "Noite",
        "disarmed": "Desarmada",
    },
    "fr": {  # French
        "armed_home": "Périmétrique",
        "armed_away": "Total",
        "armed_night": "Nuit",
        "disarmed": "Désarmée",
    },
    "de": {  # German
        "armed_home": "Perimeter",
        "armed_away": "Total",
        "armed_night": "Nacht",
        "disarmed": "Deaktiviert",
    },
    "it": {  # Italian
        "armed_home": "Perimetrale",
        "armed_away": "Totale",
        "armed_night": "Notte",
        "disarmed": "Disarmata",
    },
    "pt": {  # Portuguese
        "armed_home": "Perimétrico",
        "armed_away": "Total",
        "armed_night": "Noite",
        "disarmed": "Desarmada",
    },
}

# Multi-language alarm mode descriptions
ALARM_DESCRIPTIONS_BY_LANGUAGE = {
    "es": {  # Spanish
        "armed_home": "Activa solo la alarma perimetral (externa)",
        "armed_away": "Activa todas las alarmas (total)",
        "armed_night": "Activa la alarma nocturna (interna noche)",
        "disarmed": "Desactiva todas las alarmas",
    },
    "en": {  # English
        "armed_home": "Activates only the perimeter alarm (external)",
        "armed_away": "Activates all alarms (total)",
        "armed_night": "Activates the night alarm (internal night)",
        "disarmed": "Deactivates all alarms",
    },
    "ca": {  # Catalan
        "armed_home": "Activa només l'alarma perimetral (externa)",
        "armed_away": "Activa totes les alarmes (total)",
        "armed_night": "Activa l'alarma nocturna (interna nit)",
        "disarmed": "Desactiva totes les alarmes",
    },
    "eu": {  # Basque
        "armed_home": "Perimetroko alarma soilik aktibatzen du (kanpokoa)",
        "armed_away": "Alarma guztiak aktibatzen ditu (totala)",
        "armed_night": "Gaueko alarma aktibatzen du (barneko gaua)",
        "disarmed": "Alarma guztiak desaktibatzen ditu",
    },
    "gl": {  # Galician
        "armed_home": "Activa só a alarma perimetral (externa)",
        "armed_away": "Activa todas as alarmas (total)",
        "armed_night": "Activa a alarma nocturna (interna noite)",
        "disarmed": "Desactiva todas as alarmas",
    },
    "fr": {  # French
        "armed_home": "Active uniquement l'alarme périmétrique (externe)",
        "armed_away": "Active toutes les alarmes (total)",
        "armed_night": "Active l'alarme nocturne (interne nuit)",
        "disarmed": "Désactive toutes les alarmes",
    },
    "de": {  # German
        "armed_home": "Aktiviert nur die Perimeter-Alarmanlage (extern)",
        "armed_away": "Aktiviert alle Alarmanlagen (total)",
        "armed_night": "Aktiviert die Nacht-Alarmanlage (intern Nacht)",
        "disarmed": "Deaktiviert alle Alarmanlagen",
    },
    "it": {  # Italian
        "armed_home": "Attiva solo l'allarme perimetrale (esterno)",
        "armed_away": "Attiva tutti gli allarmi (totale)",
        "armed_night": "Attiva l'allarme notturno (interno notte)",
        "disarmed": "Disattiva tutti gli allarmi",
    },
    "pt": {  # Portuguese
        "armed_home": "Ativa apenas o alarme perimétrico (externo)",
        "armed_away": "Ativa todos os alarmes (total)",
        "armed_night": "Ativa o alarme noturno (interno noite)",
        "disarmed": "Desativa todos os alarmes",
    },
}

# Default language (fallback)
DEFAULT_LANGUAGE = "es"

# Function to get language from Home Assistant
def get_home_assistant_language():
    """Get the current Home Assistant language."""
    # For now, return Spanish as default
    # This will be overridden by the alarm control panel when it has access to hass
    return DEFAULT_LANGUAGE

# Function to get alarm names for current language
def get_alarm_names_for_language(language=None):
    """Get alarm names for the specified language or current HA language."""
    if language is None:
        language = get_home_assistant_language()
    
    # Get the language code (first 2 characters)
    lang_code = language[:2].lower()
    
    # Return names for the language, or default if not found
    return ALARM_NAMES_BY_LANGUAGE.get(lang_code, ALARM_NAMES_BY_LANGUAGE[DEFAULT_LANGUAGE])

# Function to get alarm descriptions for current language
def get_alarm_descriptions_for_language(language=None):
    """Get alarm descriptions for the specified language or current HA language."""
    if language is None:
        language = get_home_assistant_language()
    
    # Get the language code (first 2 characters)
    lang_code = language[:2].lower()
    
    # Return descriptions for the language, or default if not found
    return ALARM_DESCRIPTIONS_BY_LANGUAGE.get(lang_code, ALARM_DESCRIPTIONS_BY_LANGUAGE[DEFAULT_LANGUAGE])

# Initialize with current language
CUSTOM_ALARM_NAMES = get_alarm_names_for_language()
CUSTOM_ALARM_DESCRIPTIONS = get_alarm_descriptions_for_language()

# Alternative names you might want to use:
ALTERNATIVE_NAMES = {
    # Option 1: More descriptive names
    "descriptive": {
        "armed_home": "Alarma Perimetral",
        "armed_away": "Alarma Total",
        "armed_night": "Alarma Nocturna",
        "disarmed": "Sistema Desarmado",
    },
    
    # Option 2: Short names
    "short": {
        "armed_home": "Peri",
        "armed_away": "Total",
        "armed_night": "Noche",
        "disarmed": "Off",
    },
    
    # Option 3: Technical names
    "technical": {
        "armed_home": "ARMDAY",
        "armed_away": "ARM",
        "armed_night": "ARMNIGHT",
        "disarmed": "DARM",
    },
    
    # Option 4: Spanish names
    "spanish": {
        "armed_home": "Perimetral",
        "armed_away": "Ausente",
        "armed_night": "Noche",
        "disarmed": "Desarmada",
    },
    
    # Option 5: English names
    "english": {
        "armed_home": "Home",
        "armed_away": "Away",
        "armed_night": "Night",
        "disarmed": "Disarmed",
    }
}

# To use alternative names, uncomment one of these lines:
# CUSTOM_ALARM_NAMES = ALTERNATIVE_NAMES["descriptive"]
# CUSTOM_ALARM_NAMES = ALTERNATIVE_NAMES["short"]
# CUSTOM_ALARM_NAMES = ALTERNATIVE_NAMES["technical"]
# CUSTOM_ALARM_NAMES = ALTERNATIVE_NAMES["spanish"]
# CUSTOM_ALARM_NAMES = ALTERNATIVE_NAMES["english"] 