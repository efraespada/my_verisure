# Soporte Multiidioma para Alarmas Verisure

## 🌍 Sistema de Idiomas Automático

Tu integración **My Verisure** ahora soporta múltiples idiomas automáticamente. Los nombres y descripciones de las alarmas se adaptan al idioma configurado en Home Assistant.

### Idiomas Soportados

| Idioma | Código | Nombres de Alarma |
|--------|--------|-------------------|
| **Español** | `es` | Perimetral, Total, Noche, Desarmada |
| **English** | `en` | Home, Away, Night, Disarmed |
| **Català** | `ca` | Perimetral, Total, Nit, Desarmada |
| **Euskara** | `eu` | Perimetrala, Guztia, Gaua, Desarmatua |
| **Galego** | `gl` | Perimetral, Total, Noite, Desarmada |
| **Français** | `fr` | Périmétrique, Total, Nuit, Désarmée |
| **Deutsch** | `de` | Perimeter, Total, Nacht, Deaktiviert |
| **Italiano** | `it` | Perimetrale, Totale, Notte, Disarmata |
| **Português** | `pt` | Perimétrico, Total, Noite, Desarmada |

### 🎯 Cómo Funciona

1. **Detección Automática**: La integración detecta automáticamente el idioma configurado en Home Assistant
2. **Adaptación Dinámica**: Los nombres y descripciones se adaptan al idioma detectado
3. **Fallback Seguro**: Si el idioma no está soportado, usa español como idioma por defecto

### 📱 Configuración del Idioma en Home Assistant

Para cambiar el idioma de Home Assistant:

1. Ve a **Configuración** → **General**
2. Busca la sección **Localización**
3. Cambia el **Idioma** al que prefieras
4. **Reinicia** Home Assistant

Los nombres de las alarmas se actualizarán automáticamente.

### 🔧 Cambio Manual de Idioma

También puedes cambiar el idioma manualmente usando el servicio:

```yaml
service: my_verisure.change_language
data:
  language: "en"  # Código del idioma (es, en, ca, eu, gl, fr, de, it, pt)
```

### 📋 Ejemplos de Uso

#### Cambiar a Inglés:
```yaml
service: my_verisure.change_language
data:
  language: "en"
```

#### Cambiar a Francés:
```yaml
service: my_verisure.change_language
data:
  language: "fr"
```

#### Cambiar a Catalán:
```yaml
service: my_verisure.change_language
data:
  language: "ca"
```

### 🎨 Personalización de Idiomas

Si quieres personalizar los nombres para un idioma específico:

1. **Edita** `custom_components/my_verisure/alarm_names_config.py`
2. **Modifica** la sección `ALARM_NAMES_BY_LANGUAGE` para el idioma deseado
3. **Reinicia** Home Assistant

Ejemplo para personalizar español:
```python
"es": {  # Spanish
    "armed_home": "Mi Nombre Personalizado",
    "armed_away": "Mi Otro Nombre",
    "armed_night": "Noche",
    "disarmed": "Desarmada",
},
```

### 🔄 Actualización Automática

Cuando cambies el idioma en Home Assistant:

1. Los nombres se actualizan automáticamente
2. No necesitas reiniciar la integración
3. Los cambios se reflejan inmediatamente en la interfaz

### 🛡️ Fallback y Seguridad

- Si el idioma no está soportado → Usa español
- Si hay un error en la detección → Usa español
- Si falta el archivo de configuración → Usa valores por defecto de HA

### 📊 Estados de Alarma por Idioma

#### Español (es):
- **Perimetral**: Activa solo la alarma perimetral (externa)
- **Total**: Activa todas las alarmas (total)
- **Noche**: Activa la alarma nocturna (interna noche)
- **Desarmada**: Desactiva todas las alarmas

#### English (en):
- **Home**: Activates only the perimeter alarm (external)
- **Away**: Activates all alarms (total)
- **Night**: Activates the night alarm (internal night)
- **Disarmed**: Deactivates all alarms

#### Français (fr):
- **Périmétrique**: Active uniquement l'alarme périmétrique (externe)
- **Total**: Active toutes les alarmes (total)
- **Nuit**: Active l'alarme nocturne (interne nuit)
- **Désarmée**: Désactive toutes les alarmes

### 🔍 Verificación

Para verificar que el idioma funciona correctamente:

1. Cambia el idioma en Home Assistant
2. Ve a **Configuración** → **Dispositivos y servicios**
3. Busca tu integración "My Verisure"
4. Haz clic en el dispositivo de alarma
5. Verifica que los nombres aparezcan en el idioma correcto

### 🚀 Próximas Características

- Soporte para más idiomas
- Personalización de descripciones por usuario
- Integración con el sistema de traducciones de Home Assistant
- Detección automática de idioma del navegador 