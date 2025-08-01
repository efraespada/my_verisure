# Guía de Entidades de My Verisure

Esta guía explica las entidades que expone la integración My Verisure y cómo utilizarlas en Home Assistant.

## Entidades Disponibles

### 1. Panel de Control de Alarma
- **Entity ID**: `alarm_control_panel.my_verisure_alarm_{installation_id}`
- **Tipo**: Panel de control de alarma
- **Estados**: `disarmed`, `armed_home`, `armed_away`, `armed_night`, `arming`, `disarming`
- **Funciones**: Armar/desarmar la alarma desde la interfaz de Home Assistant

### 2. Sensores

#### General Alarm Status
- **Entity ID**: `sensor.my_verisure_alarm_status_{installation_id}`
- **Type**: Text sensor
- **States**: Detailed description of alarm status
- **Use**: To display general status in dashboards

#### Active Alarms
- **Entity ID**: `sensor.my_verisure_active_alarms_{installation_id}`
- **Type**: Text sensor
- **States**: List of active alarms
- **Use**: To see which alarms are active

#### Panel State
- **Entity ID**: `sensor.my_verisure_panel_state_{installation_id}`
- **Type**: Text sensor
- **States**: `disarmed`, `armed_home`, `armed_away`, `armed_night`, `unavailable`
- **Use**: **Perfect for automations** - uses the same states as the control panel

#### Last Updated
- **Entity ID**: `sensor.my_verisure_last_updated_{installation_id}`
- **Type**: Timestamp sensor
- **States**: Date and time of last update
- **Use**: To verify when it was last updated

### 3. Binary Sensors

#### Internal Day Alarm
- **Entity ID**: `binary_sensor.my_verisure_alarm_internal_day_{installation_id}`
- **Type**: Safety binary sensor
- **States**: `on` (alarm active), `off` (alarm inactive)

#### Internal Night Alarm
- **Entity ID**: `binary_sensor.my_verisure_alarm_internal_night_{installation_id}`
- **Type**: Safety binary sensor
- **States**: `on` (alarm active), `off` (alarm inactive)

#### Internal Total Alarm
- **Entity ID**: `binary_sensor.my_verisure_alarm_internal_total_{installation_id}`
- **Type**: Safety binary sensor
- **States**: `on` (alarm active), `off` (alarm inactive)

#### External Alarm
- **Entity ID**: `binary_sensor.my_verisure_alarm_external_{installation_id}`
- **Type**: Safety binary sensor
- **States**: `on` (alarm active), `off` (alarm inactive)

## Cómo Encontrar las Entidades

### 1. En la Interfaz de Home Assistant
1. Ve a **Configuración** > **Dispositivos y servicios**
2. Busca "My Verisure" en la lista de integraciones
3. Haz clic en la integración
4. Verás todas las entidades agrupadas bajo el dispositivo "My Verisure Alarm"

### 2. En Automatizaciones
1. Ve a **Configuración** > **Automatizaciones y escenas**
2. Crea una nueva automatización
3. En la sección de condiciones o acciones, busca "My Verisure"
4. Verás todas las entidades disponibles

### 3. En Dashboards
1. Edita tu dashboard
2. Añade una nueva tarjeta
3. Busca "My Verisure" en la lista de entidades
4. Selecciona la entidad que desees

## Ejemplos de Uso

### Automatización: Notificar cuando la alarma se arma
```yaml
automation:
  - alias: "Notificar alarma armada"
    trigger:
      platform: state
      entity_id: sensor.my_verisure_panel_state_12345
      to: "armed_away"
    action:
      - service: notify.mobile_app
        data:
          message: "La alarma se ha armado en modo ausencia"
```

### Automatización: Encender luces cuando se desarma
```yaml
automation:
  - alias: "Luces al desarmar alarma"
    trigger:
      platform: state
      entity_id: sensor.my_verisure_panel_state_12345
      to: "disarmed"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
```

### Dashboard: Tarjeta de estado de alarma
```yaml
type: entities
entities:
  - entity: sensor.my_verisure_panel_state_12345
    name: Estado de Alarma
  - entity: sensor.my_verisure_active_alarms_12345
    name: Alarmas Activas
  - entity: alarm_control_panel.my_verisure_alarm_12345
    name: Control de Alarma
```

## Servicios Disponibles

La integración también expone servicios que puedes usar en automatizaciones:

- `my_verisure.arm_away` - Armar en modo ausencia
- `my_verisure.arm_home` - Armar en modo casa
- `my_verisure.arm_night` - Armar en modo noche
- `my_verisure.disarm` - Desarmar
- `my_verisure.get_status` - Actualizar estado

### Ejemplo de uso de servicios:
```yaml
automation:
  - alias: "Armar alarma al salir"
    trigger:
      platform: state
      entity_id: person.tu_persona
      to: "not_home"
    action:
      - service: my_verisure.arm_away
        data:
          installation_id: "12345"
      
      # Desarmar al llegar
      - condition: template
        value_template: "{{ is_state('person.tu_persona', 'home') }}"
      - service: my_verisure.disarm
        data:
          installation_id: "12345"
```

## Solución de Problemas

### No encuentro las entidades
1. Verifica que la integración esté correctamente configurada
2. Reinicia Home Assistant
3. Ve a **Configuración** > **Dispositivos y servicios** > **My Verisure** y verifica que las entidades aparezcan

### Las entidades no se actualizan
1. Verifica los logs de Home Assistant para errores
2. Comprueba que la conexión con My Verisure esté funcionando
3. Usa el servicio `my_verisure.get_status` para forzar una actualización

### Error en automatizaciones
1. Asegúrate de usar el `sensor.my_verisure_panel_state_{installation_id}` para automatizaciones
2. Verifica que el `installation_id` sea correcto
3. Usa los estados exactos: `disarmed`, `armed_home`, `armed_away`, `armed_night` 