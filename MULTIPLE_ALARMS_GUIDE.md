# Guía de Alarmas Múltiples - My Verisure

## Descripción

Esta integración de My Verisure soporta la activación de múltiples alarmas simultáneamente. Esto es especialmente útil cuando quieres tener diferentes niveles de protección activos al mismo tiempo.

## Tipos de Alarma Disponibles

### Alarmas Internas
- **Interna Total**: Protección completa del interior
- **Interna Día**: Protección parcial del interior (modo día)
- **Interna Noche**: Protección parcial del interior (modo noche)

### Alarmas Externas
- **Externa**: Protección del perímetro exterior

## Estados del Control Panel

El control panel principal muestra el estado de mayor prioridad según esta jerarquía:

1. **ARMED_AWAY** (Armado Ausencia): Cuando está activa la "Interna Total"
2. **ARMED_NIGHT** (Armado Noche): Cuando está activa la "Interna Noche"
3. **ARMED_HOME** (Armado Casa): Cuando está activa la "Interna Día" o "Externa"
4. **DISARMED** (Desarmado): Cuando no hay alarmas activas

### Estados Intermedios

El control panel también muestra estados intermedios para proporcionar feedback visual durante las operaciones:

- **ARMING** (Armando): Se muestra mientras se está armando la alarma
- **DISARMING** (Desarmando): Se muestra mientras se está desarmando la alarma

Estos estados aparecen inmediatamente cuando presionas un botón y desaparecen cuando la operación se completa o falla.

## Entidades Disponibles

### 1. Control Panel Principal
- **Entidad**: `alarm_control_panel.my_verisure_alarm`
- **Función**: Control principal de la alarma
- **Atributos**: Muestra información detallada de todas las alarmas activas

### 2. Sensor de Alarmas Activas
- **Entidad**: `sensor.alarmas_activas`
- **Función**: Muestra específicamente qué alarmas están activas
- **Estados**:
  - `Desconectado`: No hay alarmas activas
  - `Interna Total`: Solo alarma interna total
  - `Interna Día`: Solo alarma interna día
  - `Interna Noche`: Solo alarma interna noche
  - `Externa`: Solo alarma externa
  - `Múltiples (X)`: X alarmas activas simultáneamente

## Ejemplos de Configuración

### Escenario 1: Solo Alarma Externa
```
Estado del Control Panel: ARMED_HOME
Sensor de Alarmas Activas: Externa
Atributos: external_active: true, alarm_count: 1
```

### Escenario 2: Alarma Interna Día + Externa
```
Estado del Control Panel: ARMED_HOME
Sensor de Alarmas Activas: Múltiples (2)
Atributos: 
  - internal_day_active: true
  - external_active: true
  - alarm_count: 2
  - active_alarms: ["Interna Día", "Externa"]
```

### Escenario 3: Alarma Interna Total + Externa
```
Estado del Control Panel: ARMED_AWAY
Sensor de Alarmas Activas: Múltiples (2)
Atributos:
  - internal_total_active: true
  - external_active: true
  - alarm_count: 2
  - active_alarms: ["Interna Total", "Externa"]
```

## Configuración de Lovelace

### Tarjeta Simple
```yaml
type: entities
entities:
  - entity: alarm_control_panel.my_verisure_alarm
    name: Control de Alarma
  - entity: sensor.alarmas_activas
    name: Alarmas Activas
```

### Tarjeta Detallada con Atributos
```yaml
type: custom:stack-in-card
cards:
  - type: entities
    title: Estado de Alarma
    entities:
      - entity: alarm_control_panel.my_verisure_alarm
        name: Control Principal
      - entity: sensor.alarmas_activas
        name: Alarmas Activas
        secondary_info: last-updated
  - type: entities
    title: Detalles de Alarmas
    entities:
      - type: attribute
        entity: sensor.alarmas_activas
        attribute: internal_day_active
        name: Interna Día
      - type: attribute
        entity: sensor.alarmas_activas
        attribute: internal_night_active
        name: Interna Noche
      - type: attribute
        entity: sensor.alarmas_activas
        attribute: internal_total_active
        name: Interna Total
      - type: attribute
        entity: sensor.alarmas_activas
        attribute: external_active
        name: Externa
```

### Tarjeta con Indicadores Visuales
```yaml
type: custom:button-card
entity: sensor.alarmas_activas
name: Estado de Alarmas
show_state: true
state:
  - value: "Desconectado"
    color: var(--disabled-text-color)
    icon: mdi:shield-off
  - value: "Interna Total"
    color: var(--error-color)
    icon: mdi:shield-lock
  - value: "Interna Día"
    color: var(--warning-color)
    icon: mdi:shield-half-full
  - value: "Interna Noche"
    color: var(--primary-color)
    icon: mdi:shield-moon
  - value: "Externa"
    color: var(--accent-color)
    icon: mdi:shield-outline
  - value: "Múltiples"
    color: var(--error-color)
    icon: mdi:shield-multiple
```

## Automatizaciones Útiles

### Notificación cuando se activan múltiples alarmas
```yaml
automation:
  - alias: "Notificar Alarmas Múltiples"
    trigger:
      platform: state
      entity_id: sensor.alarmas_activas
      to: "Múltiples"
    action:
      - service: notify.mobile_app
        data:
          title: "Alarmas Múltiples Activas"
          message: "Se han activado {{ states('sensor.alarmas_activas') }} alarmas"
```

### Cambiar iluminación según el tipo de alarma
```yaml
automation:
  - alias: "Iluminación según Alarma"
    trigger:
      platform: state
      entity_id: sensor.alarmas_activas
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: sensor.alarmas_activas
                state: "Interna Total"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.living_room
                data:
                  rgb_color: [255, 0, 0]  # Rojo
          - conditions:
              - condition: state
                entity_id: sensor.alarmas_activas
                state: "Múltiples"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.living_room
                data:
                  rgb_color: [255, 165, 0]  # Naranja
```

### Feedback visual durante operaciones de alarma
```yaml
automation:
  - alias: "Feedback durante Armado"
    trigger:
      platform: state
      entity_id: alarm_control_panel.my_verisure_alarm
      to: "arming"
    action:
      - service: light.turn_on
        target:
          entity_id: light.status_light
        data:
          rgb_color: [255, 255, 0]  # Amarillo
          brightness: 255
      - service: tts.cloud_say
        data:
          message: "Armando alarma, por favor espere"

  - alias: "Feedback durante Desarmado"
    trigger:
      platform: state
      entity_id: alarm_control_panel.my_verisure_alarm
      to: "disarming"
    action:
      - service: light.turn_on
        target:
          entity_id: light.status_light
        data:
          rgb_color: [0, 255, 0]  # Verde
          brightness: 255
      - service: tts.cloud_say
        data:
          message: "Desarmando alarma"

  - alias: "Restaurar iluminación después de operación"
    trigger:
      platform: state
      entity_id: alarm_control_panel.my_verisure_alarm
      from: 
        - "arming"
        - "disarming"
    action:
      - service: light.turn_off
        target:
          entity_id: light.status_light
```

### Notificación de progreso
```yaml
automation:
  - alias: "Notificar inicio de armado"
    trigger:
      platform: state
      entity_id: alarm_control_panel.my_verisure_alarm
      to: "arming"
    action:
      - service: notify.mobile_app
        data:
          title: "Alarma"
          message: "🔄 Armando alarma..."

  - alias: "Notificar inicio de desarmado"
    trigger:
      platform: state
      entity_id: alarm_control_panel.my_verisure_alarm
      to: "disarming"
    action:
      - service: notify.mobile_app
        data:
          title: "Alarma"
          message: "🔄 Desarmando alarma..."
```

## Solución de Problemas

### El control panel no refleja el estado correcto
- Verifica los logs para ver el estado real de las alarmas
- Comprueba que el coordinador esté actualizando los datos correctamente
- Revisa los atributos del sensor de alarmas activas

### No se muestran múltiples alarmas
- Asegúrate de que el sistema Verisure realmente soporte alarmas múltiples
- Verifica que la API esté devolviendo el estado correcto
- Comprueba los logs de depuración

## Logs de Depuración

Para activar logs detallados, añade esto a tu `configuration.yaml`:

```yaml
logger:
  custom_components.my_verisure: debug
```

Esto te permitirá ver exactamente qué datos está recibiendo la integración y cómo los está procesando. 