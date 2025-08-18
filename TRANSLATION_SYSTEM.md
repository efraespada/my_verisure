# Sistema de Traducciones para My Verisure

## 🎯 Implementación Correcta

Siguiendo las mejores prácticas de Home Assistant, hemos implementado un sistema de traducciones nativo que permite personalizar los nombres de las alarmas de forma elegante y estándar.

## 📁 Archivos de Traducción

### 1. **strings.json** (Traducción principal)
```json
{
  "entity": {
    "alarm_control_panel": {
      "my_verisure": {
        "name": "My Verisure",
        "state": {
          "armed_home": "Perimetral",
          "armed_away": "Total",
          "armed_night": "Noche",
          "disarmed": "Desarmada"
        }
      }
    }
  }
}
```

### 2. **translations/es.json** (Español)
```json
{
  "entity": {
    "alarm_control_panel": {
      "my_verisure": {
        "name": "My Verisure",
        "state": {
          "armed_home": "Perimetral",
          "armed_away": "Total",
          "armed_night": "Noche",
          "disarmed": "Desarmada"
        }
      }
    }
  }
}
```

### 3. **translations/en.json** (Inglés)
```json
{
  "entity": {
    "alarm_control_panel": {
      "my_verisure": {
        "name": "My Verisure",
        "state": {
          "armed_home": "Home",
          "armed_away": "Away",
          "armed_night": "Night",
          "disarmed": "Disarmed"
        }
      }
    }
  }
}
```

## 🌍 Cómo Funciona

### **Estructura Correcta de Traducciones**
Home Assistant requiere una jerarquía específica para las traducciones de estados:

```json
{
  "entity": {
    "alarm_control_panel": {
      "my_verisure": {
        "state": {
          "armed_home": "Perimetral",
          "armed_away": "Total"
        }
      }
    }
  }
}
```

Donde:
- `entity` → Sección para entidades
- `alarm_control_panel` → Dominio de la entidad
- `my_verisure` → Nombre de la integración (del manifest.json)
- `state` → Estados de la entidad

### **Detección Automática de Idioma**
1. Home Assistant detecta automáticamente el idioma configurado
2. Carga las traducciones correspondientes del archivo `translations/[idioma].json`
3. Si no encuentra el idioma, usa las traducciones del archivo `strings.json`

### **Estados de Alarma**
- **armed_home** → "Perimetral" (español) / "Home" (inglés)
- **armed_away** → "Total" (español) / "Away" (inglés)
- **armed_night** → "Noche" (español) / "Night" (inglés)
- **disarmed** → "Desarmada" (español) / "Disarmed" (inglés)

## 🔧 Ventajas de esta Implementación

### ✅ **Estándar de Home Assistant**
- Usa el sistema nativo de traducciones
- Compatible con todas las versiones de HA
- No requiere código personalizado complejo

### ✅ **Multiidioma Automático**
- Cambia automáticamente según el idioma de HA
- No requiere reinicio al cambiar idioma
- Soporte para múltiples idiomas

### ✅ **Mantenimiento Simple**
- Solo editar archivos JSON
- No modificar código Python
- Fácil agregar nuevos idiomas

### ✅ **Rendimiento Óptimo**
- Sin overhead de detección de idioma
- Sin imports dinámicos
- Código más limpio y eficiente
- Sin descripciones innecesarias

### ✅ **Código Simplificado**
- Eliminadas las descripciones redundantes
- Menos archivos de configuración
- Menos complejidad en el código

## 🎨 Personalización

### **Cambiar Nombres en Español**
Edita `translations/es.json`:
```json
{
  "state": {
    "alarm_control_panel": {
      "armed_home": "Mi Nombre Personalizado",
      "armed_away": "Mi Otro Nombre"
    }
  }
}
```

### **Agregar Nuevo Idioma**
Crea `translations/fr.json`:
```json
{
  "state": {
    "alarm_control_panel": {
      "armed_home": "Périmétrique",
      "armed_away": "Total",
      "armed_night": "Nuit",
      "disarmed": "Désarmée"
    }
  }
}
```

## 🔄 Aplicación de Cambios

1. **Edita** los archivos de traducción
2. **Reinicia** Home Assistant
3. **Cambia el idioma** en Configuración → General
4. **Los nombres se actualizan automáticamente**

## 📱 Dónde Ver los Cambios

- **Panel de control nativo** de Home Assistant
- **Dashboards personalizados** que usen el panel nativo
- **Interfaz de configuración** de la integración
- **Logs y estados** de las entidades

## 🛡️ Fallback y Seguridad

- Si no encuentra el idioma → Usa `strings.json`
- Si no encuentra la traducción → Usa el estado original
- Siempre funciona, nunca rompe la integración

## 🚀 Próximos Pasos

1. **Probar** que los nombres aparecen correctamente
2. **Agregar más idiomas** si es necesario
3. **Personalizar** los nombres según preferencias
4. **Documentar** para otros usuarios

Esta implementación es mucho más robusta, estándar y mantenible que la anterior. 