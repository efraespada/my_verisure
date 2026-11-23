# Automatizaciones con notificaciones de My Verisure

Esta guía describe la superficie implementada en la rama de desarrollo. Los
ejemplos y el blueprint se validan con los esquemas de Home Assistant **2026.11.2**;
su validación no ejecuta acciones ni demuestra la entrega real de cada categoría
de Verisure. La instalación y la comprobación en una instancia real se registran
por separado en la documentación de validación.

## Activar la observación

En las opciones de My Verisure, habilita la recepción de notificaciones push.
El sondeo periódico sigue funcionando como respaldo. Las opciones adicionales
tienen estos valores iniciales y dependencias:

| Opción | Valor inicial | Efecto y dependencia |
|---|---|---|
| Observar notificaciones (`notification_observation`) | Activada | Publica las dos entidades de evento de esta entrada. |
| Actualizar estados por push (`push_state_refresh`) | Desactivada | Solicita lecturas selectivas después de avisos conocidos. Requiere push. |
| Actualizar fotos externas (`external_photo_updates`) | Desactivada | Permite incorporar fotos anunciadas fuera de una petición local pendiente. Requiere push. |
| Publicar en el bus avanzado (`advanced_event_bus`) | Desactivada | Refleja el mismo contrato en `my_verisure_event`. Requiere observar notificaciones. |

Las dos actualizaciones internas pueden usarse con la observación desactivada.
Si desactivas push, desactiva primero sus opciones dependientes; el formulario
explica las combinaciones inválidas y conserva lo que has seleccionado.

Busca las entidades **Avisos** y **Resultados confirmados** en el
dispositivo de cada entrada. Sus identificadores únicos son, respectivamente,
`<config_entry_id>_notifications` y `<config_entry_id>_confirmed_results`. El
`entity_id` visible depende del nombre y del idioma de tu instalación y puede
cambiarse en HA: copia el tuyo para los ejemplos. Estas entidades permanecen
disponibles mientras la entrada esté cargada, aunque el canal push esté
desconectado. Su valor es la hora del último evento publicado, no el estado
actual de la alarma.

## Elegir el hecho que necesita la automatización

**Avisos** indica lo que se ha comunicado. Recibir un resultado de
conexión, un recordatorio o una incidencia no prueba por sí solo el estado actual
de la vivienda. **Resultados confirmados** indica un resultado que la integración
ha contrastado o terminado de guardar.

| Entidad | Tipos estables |
|---|---|
| Avisos de Verisure | `photo_reported`, `alarm_operation_reported`, `security_incident_reported`, `arm_reminder`, `unprotected_home`, `smart_disarm_notice`, `device_maintenance_notice`, `device_tamper_reported`, `maintenance_appointment`, `support_reply`, `account_notice`, `generic_notice`, `unclassified_notice` |
| Resultados verificados | `photo_ready`, `alarm_state_confirmed`, `incident_status_confirmed` |

- `photo_reported` anuncia una foto; `photo_ready` llega después de guardar las
  imágenes y completar su actualización. La foto se consulta desde la cámara,
  no desde el mensaje del evento.
- `alarm_operation_reported` no sustituye a `alarm_state_confirmed`. Este último
  puede contener el código de estado del panel y las zonas verificadas.
- `security_incident_reported` no sustituye a `incident_status_confirmed`.
  `incident_state: not_listed` solo acredita que el identificador consultado ya
  no figura en la respuesta disponible; no certifica que no exista ninguna otra
  incidencia.
- Los avisos de mantenimiento, manipulación, soporte y cuenta sirven para
  observación. No constituyen una telemetría continua de pilas, apertura de
  puertas, movimiento ni todas las funciones comerciales de Verisure.

El [catálogo de fuentes y cobertura](validation/2026-11-23-notification-catalog.json)
recoge 22 solicitudes con manejo explícito en el cliente oficial. Los 13 tipos
de aviso agrupan esas familias y reservan un tipo para mensajes desconocidos.
Que una categoría exista en ese cliente no demuestra su entrega a nuestro
receptor en todas las cuentas. Influyen el contrato, los dispositivos, los
permisos y las preferencias de notificación. El contador de cobertura de los
diagnósticos permite distinguir qué solicitudes se han recibido realmente.
Los avisos de cuenta, protección personal o sin vivienda identificable quedan
como metadatos saneados de diagnóstico cuando no pueden asociarse con seguridad
a esta instalación; no se atribuyen a la vivienda actualmente seleccionada ni
disparan sus automatizaciones.

## Contrato público, fechas y privacidad

Las entidades y el bus comparten el mismo sobre con `schema_version: 1`:

| Campo | Significado |
|---|---|
| `event_id` | Identificador local opaco del evento; útil para deduplicar acciones externas. |
| `correlation_id` | Agrupa un aviso y su resultado cuando hay una correlación conocida. No identifica al usuario. |
| `kind`, `stage`, `category`, `scope` | Tipo estable, etapa `reported` o `confirmed`, categoría y alcance validado. |
| `provider_request` | Código permitido de la solicitud original, o `null` cuando no existe. |
| `received_at` | Hora UTC de recepción local o de publicación local de un resultado verificado. |
| `occurred_at` | Hora UTC de origen solo cuando puede interpretarse con confianza; puede ser `null`. |
| `verified_at` | Hora UTC de la verificación, o `null` para un aviso sin comprobar. |
| `freshness` | `fresh`, `unknown` o `stale`; no se inventa una hora de origen ausente. |
| `delivery` | `live`, `buffered`, `restored` o `reconciled`; permite separar actividad nueva de recuperación. |
| `verification` | `notification_only`, `authoritative_read`, `image_commit` o `command_result`. |
| `subject_entity_id` | Referencia a una entidad local cuando la asociación es inequívoca; puede ser `null`. |

Según el tipo, pueden añadirse datos permitidos como `alarm_state`, las zonas
`internal_day`, `internal_night`, `internal_total` y `external`, `image_count`,
`incident_state` u `origin`. Un valor de zona `null` significa desconocido; no
debe interpretarse como desactivada. No todos los eventos incluyen esos campos.
En la entidad, `event_type` es además el atributo estándar de HA equivalente a
`kind`. En el bus se añade `config_entry_id` para seleccionar la entrada exacta.

No se publican el título y texto libre del proveedor, enlaces, imágenes, tokens,
credenciales, identificadores originales de cuenta o señal, ni ubicaciones. Los
atributos de HA pueden conservarse en Recorder y en su caché de restauración.
Los diagnósticos incluyen un anillo finito de metadatos saneados en memoria y
contadores; no son un buzón completo ni un historial duradero independiente de
Recorder. Las entradas se aíslan entre sí, incluso si usan la misma cuenta.

Cuando un resultado procede de una acción local con contexto conocido, la
entidad y el bus conservan el `Context` de esa acción en HA. Una notificación
externa no se atribuye al último usuario que actuó desde HA. El usuario real del
proveedor no se deduce del texto ni de los identificadores de correlación.

## Ejemplo: avisar cuando una foto esté guardada

Sustituye `event.mi_alarma_resultados_confirmados` por la entidad real. Este
ejemplo utiliza el disparador nativo `event.received` de HA 2026.11.2 y solo crea
una notificación local. Los datos pertenecen a `trigger.to_state.attributes`.

```yaml
alias: Verisure foto confirmada
triggers:
  - trigger: event.received
    target:
      entity_id: event.mi_alarma_resultados_confirmados
    options:
      event_type:
        - photo_ready
conditions:
  - condition: template
    value_template: >-
      {{ trigger.to_state.attributes.get('schema_version') == 1
         and trigger.to_state.attributes.get('stage') == 'confirmed'
         and trigger.to_state.attributes.get('scope') == 'installation'
         and trigger.to_state.attributes.get('freshness') == 'fresh'
         and trigger.to_state.attributes.get('delivery') == 'live' }}
actions:
  - action: persistent_notification.create
    data:
      title: Verisure
      message: Nueva foto disponible en la cámara de Home Assistant
mode: queued
max: 10
```

El [blueprint de ejemplo](../blueprints/automation/my_verisure/notification_light.yaml)
ofrece el mismo filtrado y enciende una luz al recibir el resultado verificado
que elijas. Para importarlo, copia el archivo a
`config/blueprints/automation/my_verisure/notification_light.yaml`, recarga los
blueprints y crea una automatización desde él. Selecciona la entidad **Resultados
verificados** de la vivienda y una luz de prueba. No contiene órdenes de alarma.

## Alternativa avanzada: bus de eventos

Activa la opción del bus y utiliza **una sola** de las dos vías para cada
automatización. Entidad y bus son proyecciones del mismo evento y comparten su
`event_id`; escuchar ambas provocaría dos ejecuciones de la misma acción.

Este ejemplo sustituye al anterior. Copia el identificador de tu entrada desde
los diagnósticos de la integración; no uses el identificador de otra vivienda.

```yaml
alias: Verisure foto confirmada por bus
triggers:
  - trigger: event
    event_type: my_verisure_event
    event_data:
      config_entry_id: IDENTIFICADOR_DE_TU_ENTRADA
      schema_version: 1
      kind: photo_ready
      stage: confirmed
      scope: installation
conditions:
  - condition: template
    value_template: >-
      {{ trigger.event.data.get('freshness') == 'fresh'
         and trigger.event.data.get('delivery') == 'live' }}
actions:
  - action: persistent_notification.create
    data:
      title: Verisure
      message: Nueva foto disponible en la cámara de Home Assistant
mode: queued
max: 10
```

## Reinicios, recuperación y diagnóstico

HA restaura el último valor visible de cada entidad sin convertirlo en una
notificación nueva. El buffer de arranque es limitado y se descarta como
actividad viva al cargar las plataformas; una recuperación del transporte no
debe disparar acciones como si fueran avisos nuevos. Un evento antiguo puede
seguir viéndose en Recorder o en los diagnósticos sin ser accionable. Para
acciones con efectos, exige `freshness: fresh` y `delivery: live`. Los avisos sin
hora fiable quedan `unknown`; pueden ser informativos, pero no acreditan
frescura. No hay garantía de entrega exactamente una vez ni de recepción de
todos los cambios: conserva el sondeo y usa acciones idempotentes cuando sea
posible.

La entidad de diagnóstico **Conexión de notificaciones** muestra la conexión al
transporte. Los sensores de última recepción, último aviso aceptado, último
resultado verificado, asociación del receptor y espera restante del servicio
están deshabilitados por defecto y pueden habilitarse en HA. La espera se
actualiza localmente cada 30 segundos y al vencer; no hace consultas a Verisure.

`connected: true` no acredita que Verisure haya asociado el token vigente a la
cuenta. Comprueba también `binding_state`: `disabled`, `pending`, `bound`,
`reauth_required` o `degraded`. La ausencia de un aviso no acredita que una
función esté desactivada. En un bloqueo 403/429, el cooldown compartido impide
nuevas peticiones mientras dura la espera. Otras aplicaciones de la misma IP
quedan fuera del control de admisión de esta integración.

La [auditoría y diseño](technical/notification-audit-and-design.md) y la
[especificación](../specs/notification-observability-and-automation.md) detallan
el origen del catálogo, las limitaciones y las pruebas de aceptación. Los
ejemplos de esta página se han validado como configuración estática, sin
arrancar HA, ejecutar acciones, contactar al proveedor ni modificar la alarma.
