# Configuración: cobertura de pantallas, información y funciones

Fecha: 2026-11-24. Ampliación de la [auditoría global](2026-11-24-app-capability-audit.md)
tras contrastar siete capturas aportadas por el usuario y repetir la navegación
nativa. Esta revisión documenta implementación futura, sin cambiar HA 1.1.0.

La primera revisión incluía las familias, pero no detallaba suficientemente su
presentación HA ni acreditaba cada pantalla. El hueco principal es **registrar
todos los dispositivos físicos**, además del hub y sus cámaras. Tiene ahora un
[SDD independiente](../../specs/physical-device-inventory.md); los controles se
concretan en [ajustes](../../specs/installation-and-device-settings.md),
[rutinas](../../specs/provider-routines-and-schedules.md) y
[salud/mantenimiento](../../specs/system-health-and-maintenance.md).

## Evidencia y límites del recorrido

- **N:** pantalla/formulario nativo observado en esta ampliación, sin guardarlo.
- **W:** consulta/pantalla web observada en la primera revisión del mismo día.
- **U:** las capturas del usuario muestran ese control o información.
- **S:** contrato estático, pendiente de validar el efecto y sus variantes.

Se recorrió el listado nativo completo y se abrieron fichas representativas de
panel, lector, sirena, contacto y perimetral. El fotodetector se contrastó con W/U.
Esto verifica las familias encontradas, **no todas las instancias, subtipos,
hardware o paneles posibles**. Tampoco equivale a haber probado sus escrituras.

Se abrieron la configuración general, modos del contacto, timbre individual,
Wi-Fi y formulario de otra red, Confort y su configuración, mantenimientos,
rutinas/lista/formularios/ajuste y listado de sustitución de pilas. No se envió un
formulario, se cambió un toggle, se inició una sustitución o se concedió ubicación.
El lector de QR sólo se identificó: no se abrió cámara. El detalle de salud quedó
cargando; citas y pilas no ofrecieron un caso que permitiese recorrer sus fases
posteriores. Esos límites quedan pendientes de evidencia, con cobertura sintética
prevista. No se enviaron órdenes de alarma ni nuevas solicitudes de foto.

## Menú de configuración y mantenimientos

| ID | Entrada | Evidencia | Información/funciones evaluadas | Destino y requisitos |
|---|---|---|---|---|
| CFG-01 | Mi alarma al día | N menú/home; detalle sin completar; S | Resumen de salud, diagnóstico y revisiones; no inferir salud de todos los sensores de un resumen | Diagnósticos por fuente y consulta de informes; HEALTH-1/3/6 |
| CFG-02 | Configuración de alarma/sistema | N/U | Accesos a tiempos, Wi-Fi y timbre | Acciones y entidades de configuración; SET-1…SET-7 |
| CFG-03 | Mis mantenimientos | N/S | Lista, fecha, franja, duración, tipo, suspensión y descripción de cambio de cita/aviso del técnico | Calendario/observación; cambios con contrato propio; HEALTH-5/6/7 |
| CFG-04 | Rutinas | N/W/S | Activas/inactivas, sugerencias, crear rutina/aviso, vigencia y política de notificaciones | Agenda/proyección y gestión tipada; SCHED-1…SCHED-8 |
| CFG-05 | Conéctame | N en primera revisión, menú N/U | Configuración/estado, oferta de activar servicio y dependencia de ubicación | Observación autorizada; SDK/setter pendiente; NATIVE-1/2/4/8 |
| CFG-06 | Información de dispositivos | N/U/W | Todas las filas, familias, alias, fichas y funciones propias | Registro físico completo, incluso sin entidades; INV-1…INV-8 |
| CFG-07 | Sustitución guiada de pilas | N/S | Elegibilidad, proceso, tutorial, envío/seguimiento y fases; listado sin eventos en la revisión | Diagnóstico y flujo guiado condicionado; HEALTH-3/4/5/7 |
| CFG-08 | Llaves y mandos | N/W en primera revisión, U menú | Inventario, alias, activación, seguimiento, email/push y usuarios | Gestión de accesos; ACCESS-1…ACCESS-8 |
| CFG-09 | Confort y clima | N/U menú; ajustes N | Previsión meteorológica; posible telemetría ambiental según hardware; preferencias de visualización | Sensores reales condicionados, weather opcional y dashboard HA; HEALTH-2, INV-3/4 |
| CFG-10 | Personalización/estudio de seguridad | N enlace visible | Enlace comercial/asesoramiento; no información de estado del sensor | Ruta oficial humana; ADMIN-6 |

## Inventario y fichas de dispositivos

| ID | Pantalla/control | Evidencia | Contrato futuro HA | Requisitos |
|---|---|---|---|---|
| DEV-01 | Listado interior y perimetral completo | N/W | Ficha por aparato; no filtrar sólo YP/YR, activos o remoteUse | INV-1/2/6 |
| DEV-02 | Alias y descripción de cada ficha | N/U/W | Familia/modelo cuando estén probados; información descriptiva no es telemetría en vivo | INV-3/4 |
| DEV-03 | Editor de nombre/pencil | N lector, U contacto, S setter | Alias remoto editable y confirmado; personalización HA independiente | INV-5, SET-7 |
| DEV-04 | Fotodetector: modos y última foto | W/U; S | Cámara ya existente con identidad conservada; modos de configuración; foto nueva sólo explícita | INV-4/7, SET-3/6 |
| DEV-05 | Contacto/Shocksensor: modos y timbre | N/U | Ficha propia, switches día/noche y timbre si sus contratos lo permiten; no inventar apertura instantánea | INV-4, SET-1/3/4 |
| DEV-06 | Unidad central: alias e información | N | Panel físico relacionado con hub sin duplicación; ajustes de red/tiempos por capacidad | INV-1/2/5, SET-1/2/5 |
| DEV-07 | Lector: alias e información | N | Ficha sin exigir entidades ficticias; flags/PIN sólo si se prueban para ese modelo | INV-1/3/4/5, SET-1/4 |
| DEV-08 | Sirena: alias e información | N | Ficha física; no entidad siren actuable por una descripción del producto | INV-1/3/4/5 |
| DEV-09 | Perimetral: alias, foto y participación fija | N | Ficha/cámara cuando proceda; no editor día/noche cuando la participación exterior es fija | INV-3/4, SET-1/3 |
| DEV-10 | Total fijo, parcial día y parcial noche | N contacto, W/U fotodetector | Dos booleanos independientes; preservar 00/01/10/11; total de sólo lectura si fijo | SET-3/6 |

Los identificadores de registro deben seguir la identidad del aparato, no su alias
ni su posición en la lista. En 1.1.0 `device.py` registra el hub por entrada y las
cámaras usan ese mismo DeviceInfo; la lista de dominio no es aún un registro
físico completo. INV-7 exige preservar entidades y validar targets por dispositivo
antes de migrar sus asociaciones. Reutilizar un alias no une lector y sirena.

## Tiempos, timbre y Wi-Fi

| ID | Pantalla/control | Evidencia | Contrato futuro HA | Requisitos |
|---|---|---|---|---|
| SETUI-01 | Tiempos desde el listado de dispositivos | N botón; W editor | La misma capacidad de configuración, evitando duplicar valores o consultas | SET-2 |
| SETUI-02 | Modificar tiempos desde configuración del sistema | N menú; W lectura/WAIT/OK; S | Cuatro campos legacy o particiones por panel, rangos efectivos y confirmación | SET-1/2/6 |
| SETUI-03 | Timbre global/lista y acceso desde una ficha | N/U | Ámbito de sensor correcto: la ficha filtra uno, la lista general varios | SET-1/4/6 |
| SETUI-04 | Campana del panel y sonido del sensor | N/U explicación; S flags | Modelar dependencia y unknown; guardado no demuestra sonido efectivo | SET-4 |
| SETUI-05 | Red en uso y redes disponibles | N/U; W consultas; S | Lectura bajo demanda, antigüedad y fuerza si tiene fuente; SSID privado | SET-5 |
| SETUI-06 | Permiso de ubicación para escanear | N/U, rechazado | No requerido para el flujo manual HA; no escaneo ficticio desde Linux | SET-5 |
| SETUI-07 | Añadir otra red: SSID, password, seguridad | N; S setter/status | Cambio Wi-Fi manual privado, tipos permitidos, confirmación y manejo de conectividad ambigua | SET-5/6 |
| SETUI-08 | Escanear QR | N botón; S bridge | Comodidad de frontend condicionada; no bloquear SSID manual ni abrir cámara automáticamente | SET-5 |

Los dos accesos de tiempos tienen nombres distintos en UI y deben mapearse a
una intención de dominio común. La confirmación del contrato por generación de
panel sigue pendiente para escritura. Los controles día/noche son configuración
de participación; no arman. Las lecturas radio se agrupan y se hacen bajo demanda.

La UI de Wi-Fi observada ofrecía red abierta y WPA2: son opciones de ese cliente,
no una lista universal de seguridad admitida. No se rellenó contraseña, se escaneó
QR ni se pulsó Conectar. El permiso de ubicación fue cancelado y el formulario
manual siguió disponible. La contraseña futura no circulará por eventos o trazas.

## Confort, mantenimientos, rutinas y pilas

| ID | Pantalla/control | Evidencia | Contrato futuro HA | Requisitos |
|---|---|---|---|---|
| OTHER-01 | Confort: previsión y días siguientes | N | Weather opcional de fuente legítima; nunca confundir sus grados/humedad con sensores interiores | HEALTH-2 |
| OTHER-02 | Confort: mostrar inicio/previsión y restablecer | N | Preferencias de dashboard HA; no control de climatización ni cambios del móvil | HEALTH-2, NATIVE-5 |
| OTHER-03 | Lista de mantenimientos | N sin cita editable; S campos | Calendario, próxima visita, estado suspendido y timestamps coherentes | HEALTH-5/6/7 |
| OTHER-04 | Reprogramar visita/franjas/técnico en camino | UI describe; S lectura de capacidad; flujo no recorrido | Administración condicionada a contrato/permiso; notificación reportada separada de cita confirmada | HEALTH-5/6/7 |
| OTHER-05 | Rutinas: sugerencias/lista/onboarding | N | Sugerencia no equivale a rutina creada ni activa; cancelar no crea | SCHED-1/4/7 |
| OTHER-06 | Formulario de nueva rutina | N/S | Nombre, modo objetivo, hora, días, vigencia y duración indefinida; timezone y confirmación | SCHED-1/3/5/7 |
| OTHER-07 | Formulario de nuevo aviso | N/S | Condición de modo distinto, hora/días/vigencia; aviso sin orden de alarma | SCHED-1/3/4 |
| OTHER-08 | Rutinas: notificar sólo fallo | N, setter no capturado | Preferencia proveedor separada del filtro de eventos HA; no mutar mientras falte contrato | SCHED-8 |
| OTHER-09 | Pilas: lista de eventos | N lista vacía; S dos variantes de DIYList | Elegibilidad, estado, días y pasos; sin convertir lista vacía en pilas llenas | HEALTH-3/4/7 |
| OTHER-10 | Pilas: inicio, pasos, tamper, validación y cierre | S; no caso elegible en UI | Flujo manual protegido, sin suspender protección por polling | HEALTH-3/4/7 |
| OTHER-11 | Pilas: envío, recibido, rechazo, reenvío y seguimiento | S; detalle no recorrido | Observación privada y acciones explícitas revisadas; no pedidos automáticos | HEALTH-5/7 |

En el cliente público recuperado **DIYInit y DIYCheck son mutaciones**. La
descripción anterior agrupaba mal ese ejemplo al hablar de queries con efectos;
queda corregida. La seguridad se decide por intención: una lectura radio puede
iniciar trabajo de consulta del panel, pero no por ello equivale a iniciar un DIY.

## Variantes del contrato y cierre de cobertura

La primera extracción conservaba una firma por nombre de operación: **263 nombres
únicos**, no todas las variantes de selección. El barrido adicional de las mismas
doce fuentes recuperó **278 variantes textuales en 295 apariciones**. `xSDeviceList`
tiene siete variantes; una lista con sólo tipos no puede usarse como inventario
completo ni para retirar dispositivos. El [JSON](../validation/2026-11-24-app-capabilities.json)
conserva ahora hashes, selecciones, variables y ubicaciones de cada variante,
sin incorporar el código completo o datos de la vivienda.

El número de firmas no prueba que se hayan visto todas las pantallas del cliente.
Esta matriz permite comprobar cada fila y sus límites, incluidos módulos no
cargados y setters aún no capturados. La configuración para notificar sólo fallos
es un ejemplo visible cuyo transporte sigue pendiente pese al inventario estático.

Requisitos nuevos: INV-1…INV-8 y SCHED-8. El catálogo pasa a cinco baselines y
**once SDDs Draft**, con **84 requisitos futuros trazados**. Los presupuestos de
tests son planes, no pruebas de implementación. Mantener matrices sintéticas de
familia/capacidad, 00/01/10/11, campana desconocida, permisos denegados, secretos,
listas parciales, migración/targets, agenda, DST y procesos sin elegibilidad.

Antes de Ready: validar las escrituras de cada familia, identidad por panel,
setters desconocidos, fuentes ambientales y casos elegibles de mantenimiento.
Los pasos que exijan operación física o reducción de protección se revisan por
separado; no se ejecutan para poder marcar una fila como «observada».
