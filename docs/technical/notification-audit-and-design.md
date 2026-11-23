# Auditoría y propuesta de notificaciones en Home Assistant

Fecha: 2026-11-23. Base auditada: `develop`, commit
`29c35620bf17de631191664fdd4e9ed08643aff2`.
Estado histórico de la auditoría: investigación sobre el commit indicado.
La propuesta fue aprobada después y está implementada en esta rama; consulta el
[SDD actualizado](../../specs/notification-observability-and-automation.md), la
[guía de automatizaciones](../automation-notifications.md) y el
[recibo de implementación](../validation/2026-11-23-notification-implementation.json).
Las reproducciones descritas abajo corresponden a la base anterior a las correcciones.

La propuesta es ofrecer dos entidades de evento por instalación: **Avisos de
Verisure** y **Resultados confirmados**, con diagnóstico del canal por separado.
Un mismo módulo de notificaciones alimentaría las cámaras, esas entidades y un
planificador de consultas limitadas. Antes de añadir consultas espontáneas hay
que corregir los problemas de concurrencia, bloqueo y persistencia descritos aquí.

## Qué se ha comprobado

Se han inspeccionado el cliente público web 3.8.0, su puente de mensajes nativos,
los textos de interfaz españoles y las ayudas oficiales de Verisure. El paquete
nativo instalado identifica la versión 10.192.1, compilación 3. Su interfaz no
respondió a la inspección de accesibilidad; la web mostró el acceso de usuario.
No se inició otra sesión ni se consultó el buzón privado.

El [recibo del catálogo](../validation/2026-11-23-notification-catalog.json)
conserva fuentes, hashes, módulos, 53 nombres de solicitud declarados, 22 con
tratamiento explícito en el gestor de push y 21 destinos de navegación estática
(los grupos se solapan). La entrega real ya demostrada a HA sigue siendo la de
fotos; el código de un manejador demuestra que el cliente entiende una categoría,
pero no que nuestro receptor independiente la reciba en esta cuenta.

## Catálogo y comportamiento del cliente oficial

| Familia | Códigos de solicitud | Comportamiento verificado en el cliente |
|---|---|---|
| Fotos | `INF` | Consulta la miniatura por señal exacta y permite abrir su galería. Es la familia recibida y validada previamente en HA. |
| Resultado de conexión o desconexión | `ARMDISARM` | Interpreta resultado y excepciones de la operación. Tras confirmar el diálogo de éxito consulta el estado actual; una excepción abre su flujo de gestión. |
| Incidencia atendida por la central | `SMARTNOT` | Actualiza la lista de incidencias abiertas, muestra el aviso y abre el informe. La disponibilidad depende del servicio; las condiciones oficiales lo reservan al titular. |
| Recordatorio de protección | `SCHCD` | Consulta el estado, lo muestra y ofrece cambiar la conexión. Recibir el mensaje no conecta la alarma automáticamente. |
| Conéctame y desconexión inteligente | `UNPROTECTED`, `SMARTDISARM` | Abren sus respectivos diálogos y comprueban el estado. La traducción de Smart Disarm comunica que la alarma ya está desconectada; su condición de origen no se ha verificado. |
| Pilas y mantenimiento guiado | `DIY`, `DIYKEYS`, `DIYREMINDER`, `DIYTRACKING` | Avisos de sustitución, recordatorios y navegación al seguimiento del proceso o envío. |
| Manipulación sin restablecer | `DIYTAMPER_DIY`, `DIYTAMPER_NO_DIY` | Muestran instrucciones asociadas a un dispositivo con señal de manipulación pendiente. No equivalen a un estado continuo de todos los sensores. |
| Citas | `MAINTENANCE`, `RSCHAFTERSUSPEND` | Muestran mantenimiento y acceso a reprogramación. |
| Soporte | `ANSWER`, `CHATHELP` | Presentan una respuesta o abren la ayuda. |
| Aviso genérico | `NOT`, `PWC` | Presentan título y texto. No se infiere el significado de `PWC` a partir de sus siglas. |
| Cuenta y otras áreas | `AUTHTESTMODE`, `IND`, `FAMILIES`, `INVITATIONACCEPTED` | Prueba de dispositivo de confianza, navegación e invitaciones de protección personal. Necesitan un alcance distinto al de una vivienda. |

La [ayuda de usuarios](https://www.verisure.es/cliente/datos?panel=fast) confirma
que los avisos de actividad pueden requerir activar seguimiento y notificaciones
push para cada usuario. Los campos correspondientes también existen en el
cliente. Esta investigación no ha consultado ni cambiado su configuración.

La [ayuda de dispositivos](https://www.verisure.es/cliente/dispositivos) describe
avisos por pilas bajas y cortes eléctricos. El catálogo de actividad del cliente
también incluye humo, agua, inhibición y su recuperación, sabotaje, condiciones
ambientales, cerraduras y errores de operaciones. Ese catálogo tiene códigos
numéricos propios (216 nombres): **no es un catálogo demostrado de mensajes FCM**. No se deben
confundir esos números con `push.type`, `request` o el tipo de una señal de foto.

Conéctame, recordatorios y SmartNotifications están descritos en la
[configuración oficial](https://www.verisure.es/cliente/configuracion-sistema) y
las [condiciones de la app](https://customers.verisure.es/media_contents/app/myverisure/android/terms_es_verisure.html).
Contrato, panel, dispositivos, permisos y configuración condicionan la
disponibilidad. No se ha establecido un flujo continuo de cada apertura de
puerta, movimiento PIR, porcentaje de batería o medida ambiental por push.
Incluso `idSignal` cambia de función: identifica una señal de imagen en `INF` y
una incidencia en el recorrido `SMARTNOT`. Cada familia necesita su propio esquema.

## Auditoría del recorrido actual

Las reproducciones usaron exclusivamente respuestas sintéticas. El
[recibo de auditoría](../validation/2026-11-23-notification-audit.json) identifica
la base, comandos y resultados. Los problemas siguientes siguen sin corregir en
esta rama de documentación.

| Prioridad | Hallazgo | Evidencia e implicación |
|---|---|---|
| P1 | Una lectura antigua puede sobrescribir la confirmación de un comando. | `coordinator.py:276` publica al terminar sin una generación de estado. Se pausó una lectura, se aplicó un resultado sintético confirmado y la lectura posterior revirtió el estado publicado. Añadir push aumentaría las oportunidades de esta carrera. |
| P1 | El cooldown no se comprueba en la admisión de todas las solicitudes. | `core/api/base_client.py:98` envía incluso con bloqueo activo. La simulación de 403 registra bloqueo; la de 429 se trata como error genérico. El control del coordinador no cubre todos los clientes, bucles ni entradas. |
| P1 | Los comandos de una instalación no están serializados. | `coordinator.py:405` no tiene exclusión para toda la operación. Un comando compuesto interior y perímetro puede entrelazarse con otro. Hallazgo de código, sin prueba física. |
| P2 | Una escritura cancelada puede sobrescribir otra más reciente. | `core/api/push_storage.py:34` libera el lock al cancelar la espera del hilo, que sigue escribiendo. La reproducción determinista acaba guardando la versión anterior. Proteger solo la espera con `shield` no conserva por sí mismo la propiedad del lock. |
| P2 | La caché acepta material criptográfico inválido. | `core/api/push_receiver.py:143` comprueba cadenas no vacías, pero no la validez de la clave DER, el punto público o el secreto. La reproducción acepta claves corruptas; conexión y descifrado deben observarse por separado. |
| P2 | El refresco denominado solo de alarma puede ampliarse. | `coordinator.py:284` permite un refresco completo. `core/api/alarm_client.py:134` puede iniciar `CheckAlarm` y sondeos de radio ante un estado desconocido. No es el recorrido adecuado para cada aviso espontáneo. |
| Alcance actual | El receptor está acoplado a una foto pendiente. | `photo_notifications.py:50` descarta el resto y admite únicamente `INF/type=0`. Es una limitación deliberada del alcance actual. |
| Ciclo de vida | El transporte empieza antes que las plataformas. | `push.py:47` prepara recepción antes de que `integration.py:71` publique el runtime y cargue entidades. La ampliación necesita un estado explícito de preparación y un buffer limitado. |
| Observabilidad | Recibido, conectado y actualizado representan hechos distintos. | El contador aumenta antes de validar el evento. La caché puede devolverse como refresco exitoso; una rotación FCM puede quedar pendiente de asociación con Verisure. Ninguno de esos hechos acredita por sí solo el estado actual de la casa. |

Hay además dos límites de robustez: el ACK del SDK no espera una transacción con
la persistencia/publicación de HA, y su lectura protobuf ocurre antes de nuestra
cota del sobre descifrado. No se promete entrega exactamente una vez; la segunda
cuestión requiere endurecer el SDK o su adaptador, sin afirmar una explotación.

Se conservan las medidas existentes: TLS, descifrado autenticado, filtro del
proyecto remitente, estado privado 0600, reutilización de credenciales, backoff,
cancelación de tareas y sondeo de respaldo. El remitente identifica el proyecto;
la instalación y el alcance se validan además en el consumidor.

## Diseño recomendado para HA

### Una recepción y dos entidades de evento

Un módulo general validaría y clasificaría una sola vez. Tras deduplicar,
entregaría el aviso a consumidores independientes mediante una interfaz pequeña:
fotos pendientes, observación HA y planificación de consultas. El consumidor
fotográfico conservaría su correlación actual y no compartiría una cola lenta
con el historial o las consultas HTTP.

- **Avisos de Verisure:** `photo_reported`, `alarm_operation_reported`,
  `security_incident_reported`, `arm_reminder`, `unprotected_home`,
  `smart_disarm_notice`, `device_maintenance_notice`, `device_tamper_reported`,
  `maintenance_appointment`, `support_reply`, `account_notice`, `generic_notice`
  y `unclassified_notice`.
- **Resultados verificados:** `photo_ready`, `alarm_state_confirmed` e
  `incident_status_confirmed`. Una foto solo está lista tras guardar todas sus
  imágenes y el marcador de finalización; un estado exige una respuesta vigente
  de su fuente autoritativa.

Los nombres son contratos propuestos. La integración actual no publica esas
entidades. Las [entidades de evento de HA](https://www.home-assistant.io/integrations/event/)
permiten observar sucesos y crear automatizaciones. La implementación debe
mantenerlas disponibles mientras su entrada esté cargada; el estado de la
conexión se muestra en diagnósticos separados. Así el primer evento real tras
reconectar no queda oculto por una transición desde `unavailable`.

### Datos estables y privacidad

El contrato lleva versión, identificador local opaco, correlación, categoría,
etapa, alcance, hora de recepción, hora de origen opcional, hora de verificación cuando exista,
frescura, entrega y
método de verificación. Los identificadores de señales, instalaciones, usuarios
y mensajes del proveedor se resuelven internamente; pueden proyectarse referencias
a entidades locales de HA cuando sean inequívocas.

El título y cuerpo arbitrarios, `advancedInfo`, enlaces, invitaciones, ubicación,
tokens e imágenes no se copian a atributos. HA guarda atributos de eventos en
Recorder y en su almacenamiento de restauración. Las descripciones visibles se
generan con plantillas locales y datos explícitamente permitidos. Las categorías
nuevas se muestran como no clasificadas, sin ejecutar consultas o interpretar
texto libre como una orden.

La primera versión utilizaría Recorder/Actividad para el historial normal y un
anillo en memoria de metadatos saneados para diagnóstico. No necesita un segundo
buzón permanente con mensajes completos. Un diario privado independiente solo
tiene sentido si se requiere retención sin Recorder: sería opcional, finito y
sin cuerpos originales. Un exportador avanzado al bus `my_verisure_event` sería
también opcional y reflejaría exactamente el mismo contrato; las automatizaciones
deberían elegir una única entrada para evitar acciones duplicadas.

### Consultas selectivas y presupuesto

El aviso se muestra sin consultar toda la instalación. Solo los manejadores
documentados solicitan recursos concretos. El planificador agrupa durante dos
segundos, mantiene una tarea pendiente por recurso y limita inicialmente a un
inicio de reconciliación de fondo por cuenta cada 30 segundos. Son decisiones de
diseño conservadoras, no límites publicados por Verisure ni una garantía de latencia.

Todos los clientes HA deben compartir la admisión HTTP y el cooldown de 403/429,
incluido `Retry-After` válido. Cada solicitud en vuelo consume su permiso; no se
retiene un lock HTTP durante las pausas de sondeo. Los comandos explícitos tienen
prioridad y exclusión por instalación; una generación impide publicar lecturas
anteriores. Una confirmación ya obtenida por HA puede satisfacer la reconciliación
sin consultar otra vez. La admisión se coordina también por origen; un bloqueo confirmado por IP se
comparte entre las entradas afectadas. Otras apps y dispositivos siguen fuera de
este control.

Los refrescos espontáneos de alarma usarían un lector nativo sin `CheckAlarm`
automático. Un código desconocido permanece desconocido. La cámara conserva su
intervalo de respaldo de 20 segundos. Las fotos originadas en otra app podrían
recuperarse con una opción independiente, consultando la señal exacta y
validando cámara/fecha. Atender un aviso nunca inicia otra captura.

### Reinicios, fallos y datos históricos

La recepción anterior a la preparación de HA usa un buffer de 64 registros y
128 KiB. Su contenido histórico no se publica después como actividad nueva.
Las pérdidas por desbordamiento se cuentan; la pista de una foto pendiente no
depende de ese buffer de presentación. El historial restaurado tampoco vuelve
a dispararse. Eventos antiguos o sin fecha verificable conservan esa condición;
la hora de recepción no se transforma en fecha de origen.

Un aviso conocido y bien asignado que no incluya fecha puede marcar una única
reconciliación limitada del recurso; su recepción no acredita un estado actual.
Los tipos desconocidos no generan consultas. Las lecturas que repiten el mismo
estado no emiten otro evento confirmado. La primera lectura y la recuperación
tras una caída se identifican como reconciliación, sin presentar el cambio físico
como recién ocurrido.

Tras una caída se realiza una reconciliación agrupada del estado actual. No hay
un endpoint de recuperación completa del historial de push verificado en esta
investigación. El sondeo permanece como respaldo y no garantiza reconstruir cada
suceso perdido. Una automatización de estado utiliza resultados verificados;
una respuesta de soporte o recordatorio puede justificar directamente un aviso
informativo al usuario. No se provocan armados ni otros comandos al recibirlos.

## Qué podrá observar y automatizar el usuario

- Avisar de una nueva foto cuando esté guardada y disponible en HA.
- Actualizar el panel y sus automatizaciones cuando se confirme un cambio hecho
  desde otra app o el teclado, si esa categoría llega al receptor.
- Mostrar una incidencia abierta y sus cambios de estado cuando la cuenta y
  servicio permitan la consulta.
- Crear avisos de pilas, mantenimiento y recordatorios sin una consulta general
  adicional por cada mensaje.
- Ver conexión FCM, última recepción válida, asociación pendiente, duplicados,
  descartes, cooldown y antigüedad de la última lectura autoritativa. La ausencia
  de avisos durante un periodo tranquilo no es una avería.

El diagnóstico incluiría cobertura por categoría: conocida en el cliente,
servicio disponible cuando se conozca, entrega observada y verificación soportada.
Así se puede consultar qué está probado en esta instalación sin presentar el
catálogo completo del proveedor como funciones ya disponibles en HA.

Guardián, familias y notificaciones de cuenta necesitan contratos de alcance y
permisos propios antes de asignarlos a una vivienda. Las alertas ambientales,
cerraduras y todos los sensores se incorporarán únicamente al demostrar sus
mensajes y fuentes; un nombre en el catálogo de actividad no crea una entidad.

## Ejemplo de automatización propuesto

Este ejemplo requiere la futura entidad de resultados. Validar el esquema con
el SDK local no demuestra que esa entidad exista ni ejecuta su acción.

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
      {{ trigger.to_state.attributes.get('freshness') == 'fresh'
         and trigger.to_state.attributes.get('delivery') == 'live' }}
actions:
  - action: persistent_notification.create
    data:
      title: Verisure
      message: Nueva foto disponible
mode: queued
max: 10
```

La misma selección por categoría permitiría avisos de mantenimiento o incidencias.
No se deduce presencia física a partir de una conexión/desconexión remota.
Las automatizaciones deben seleccionar etapa y tipo concretos: enlazar cualquier
aviso con una nueva petición de fotos podría crear un ciclo. Se conservará el
contexto de una petición local cuando se conozca; no se inventará el usuario o
la app que originó un evento por coincidir cámara y hora.

## Secuencia de implementación propuesta

1. **Corregir la base:** generaciones y comandos seriales, admisión/cooldown
   compartidos, persistencia resistente a cancelación y validación criptográfica.
2. **Observar sin consultas añadidas:** normalizador, deduplicación, preparación,
   entidades de evento, diagnósticos, restauración y privacidad. Mantener fotos.
3. **Verificar resultados:** emitir foto lista después del guardado y añadir
   reconciliación limitada de alarma/incidencias con contratos de consulta reales.
4. **Ampliar familias:** seguimiento de usuarios, mantenimiento y recuperación de
   fotos externas; después cuenta/protección personal según evidencia y permisos.
5. **Facilitar uso:** ejemplos, panel de eventos y blueprints de avisos. Validar
   casos perdidos/duplicados y coste de llamadas antes de ampliar activaciones.

El [SDD propuesto](../../specs/notification-observability-and-automation.md)
define requisitos, configuración, pruebas y aceptación. Esta auditoría no cambia
la integración en ejecución, no habilita servicios ni autoriza pruebas físicas
de interior total. Las 34 regresiones existentes del área pasan; las
reproducciones nuevas muestran defectos presentes, no correcciones realizadas.

## Seguimiento de la propuesta aprobada

La implementación corrige la admisión HTTP, el orden de publicación y la
persistencia cancelada. Añade eventos saneados y confirmaciones independientes,
recuperación sin reproducir automatizaciones antiguas y replay privado de fotos
e incidencias. Las consultas opcionales respetan agrupación de dos segundos,
inicios separados por 30 segundos y un máximo de 32 recursos pendientes.
Ningún aviso inicia comandos de alarma, capturas ni confirmaciones de incidencias.
El [recibo de implementación](../validation/2026-11-23-notification-implementation.json)
registra las verificaciones posteriores; los defectos descritos arriba corresponden
al commit base original. Las categorías todavía no recibidas no se presentan
como entregas reales verificadas.
