# Auditoría funcional de My Verisure y ampliación futura de Home Assistant

Fecha: **2026-11-24**. Resultado: evaluación y SDDs; **sin implementación nueva**.
Base del repositorio: `6071af502dbe3fa0a035ce9b0469ba244139ce4d`, integración 1.1.0.
Cliente web español observado: **3.8.0**. App macOS/WebView: **10.192.1, build 3**.

La ampliación más útil es llevar a HA la observación y la gestión tipada de
accesos, configuración, actividad, salud y rutinas. Cámaras conectadas,
cerraduras y protección personal requieren contratos y hardware adicionales.
Compras, consentimientos, emergencias y permisos propios del teléfono conservan
sus flujos oficiales. No todo botón de la app debe convertirse en una acción HA.

## Alcance y método

Se revisaron por separado la web autenticada y la app instalada. En la web se
abrieron instalación, dispositivos, llaves, usuarios, tiempos, sonidos, red y
participación de sensores en modos. En la app se revisaron además Conéctame,
buzón, preferencias, perfil y autorización del terminal. Los editores se cerraron
sin guardar. Se contrastaron sus contratos con los recursos públicos del cliente
y con las guías oficiales españolas enlazadas al final.

El [inventario reproducible](../validation/2026-11-24-app-capabilities.json) recoge:

- **263 documentos GraphQL distintos**, recuperados del bundle principal y once
  módulos públicos cargados durante la navegación; firma, variables tipadas,
  campo raíz, hash, fuente y familia asignada para cada uno.
- **152 comandos de puente nativo**, distribuidos en veinte handlers. Un comando
  JavaScript → SDK nativo **no es un endpoint HTTP utilizable desde Linux**.
- Identidad y SHA-256 de las doce fuentes públicas, diferencias observadas entre
  clientes y decisiones de exposición HA. No incluye respuestas de la vivienda,
  credenciales, tokens, identificadores domésticos ni capturas de tráfico.

Se observaron 29 peticiones GraphQL web, correspondientes a 17 operaciones
distintas, incluidas consultas de estado WAIT/OK. Se enviaron **cero órdenes de
alarma, cambios de configuración, autorizaciones de terminal o capturas nuevas**.
No se generó una nueva captura HAR nativa: la evidencia nativa de esta auditoría
es navegación UI y contrato estático del puente, no confirmación de su transporte.
La prohibición de probar interior total se mantiene.

### Qué significa la evidencia

| Nivel | Qué permite afirmar | Qué sigue pendiente |
|---|---|---|
| UI observada | La función o formulario apareció en ese cliente/cuenta | No acredita todos los roles, paneles o efectos del guardado |
| Consulta observada | Se vio esa petición y, cuando terminó, su forma de respuesta | No valida su mutación pareja ni todos los casos de error |
| Contrato estático | La versión inspeccionada declara una operación o comando | No prueba servicio contratado, acceso, transporte SDK o hardware disponible |
| Guía oficial | Verisure describe una capacidad y sus condiciones generales | No sustituye un contrato API ni una prueba técnica |
| Propuesta HA | Decisión de diseño para una futura implementación | No significa que exista una entidad o acción instalada |

La cobertura es completa **respecto a los 263 documentos y 152 comandos
recuperados**, todos clasificados. No es una afirmación de haber descubierto todos
los módulos diferidos, países, SDKs, modelos de cámara o funcionalidades futuras.
Los huecos identificados son puertas de aceptación de los SDDs, no endpoints
inventados. Tampoco se atribuye soporte implementado a cada variante de una
operación por coincidir con una de las cinco capacidades existentes.

## Diferencias concretas entre web y app

| Superficie | Observación | Consecuencia para HA |
|---|---|---|
| Configuración | **Conéctame** apareció en el menú nativo y no en el menú Chrome observado | Revisar servicio y bridge; no limitar el inventario al menú web |
| Buzón | Visible en la app; la misma ruta normal en Chrome terminó en «Page unauthorised» | No falsear plataforma. Falta establecer una API legítima de buzón para Linux |
| Llaves | Los dos editores mostraron alias, activación, seguimiento y avisos email/push equivalentes | El contrato de llaves sirve de base, conservando variantes de panel y flags |
| Perfil/terminal | La app autenticada ofrecía todavía «Autorizar este terminal» | Login, asociación FCM y autorización de alta seguridad son estados distintos |
| Preferencias | Sesión persistente, huella, confirmación, voz, BASIC, aspecto y privacidad | Parte tiene equivalentes HA; parte depende del SO y se queda en el móvil |
| Multimedia | El cliente declara `xsCameras.*` además de GraphQL | Streaming, SD y configuración necesitan adaptador de familia/SDK, no sólo más queries |
| Protección personal | Puentes de ubicación, familias, SOS, Acompáñame y accidente | El ámbito persona/cuenta no puede asignarse arbitrariamente a una instalación |

La denegación de la ruta web del buzón es una observación del cliente normal,
no una prueba de que cualquier API subyacente sea universalmente inaccesible.
No se cambiaron flags nativos ni se amplió autorización para evitar esa pantalla.

## Matriz de todas las familias evaluadas

Decisiones: **actual** = capacidad existente con los límites de su baseline;
**P1** = candidata prioritaria; **P2** = condicionada a protocolo/hardware/servicio;
**P3** = administración privada e interactiva; **oficial** = mantener el flujo en
la app. Las entidades y acciones siguientes son propuestas, no nombres públicos
ya disponibles. P1 tampoco implica que la implementación esté lista sin revisión.

| Función de la app | Decisión y encaje HA | Evidencia / condición principal | SDD |
|---|---|---|---|
| Login, SMS, sesión persistente y cambio de instalación | Actual; preservar UUID y sesión por entrada | Baseline; no equivale a terminal de alta seguridad | [Autenticación](../../specs/native-authentication-and-session-lifecycle.md) |
| Armado exterior, parcial noche, total y desarmado | Actual; preservar mapeos y perímetro complementario | Total reservado al propietario para pruebas físicas | [Alarmas](../../specs/alarm-modes-and-confirmation.md) |
| Estado de panel/zonas e instalación/dispositivos | Actual; ampliar metadatos sólo si tienen utilidad | Nullable, roles y tipos por panel | [Datos e identidad](../../specs/installation-cameras-and-entity-identity.md) |
| Fotos de fotodetectores, miniaturas y actualización | Actual; conservar captura explícita y almacenamiento privado | No confundir foto existente con captura nueva | [Datos e identidad](../../specs/installation-cameras-and-entity-identity.md) |
| Notificaciones push, eventos y resultados verificados | Actual; ampliar fuentes sin duplicar receptor | Entrega por categoría/servicio no garantizada | [Notificaciones](../../specs/notification-observability-and-automation.md) |
| Capacidades, permisos y servicios contratados | P1; base de descubrimiento, sin controles ficticios | Rol/servicio/panel positivos, unknown preservado | [Base común](../../specs/app-management-foundation.md) |
| Inventario de llaves y mandos | P1; lectura, estado y alias de configuración | UI y lectura; identidad estable de llave/slot | [Accesos](../../specs/access-control-and-users.md) |
| Activar/desactivar llave, alias y reasignación | P1; acciones o controles de configuración autorizados | Patch vigente, permiso, confirmación, posible resultado parcial | [Accesos](../../specs/access-control-and-users.md) |
| Seguimiento y avisos email/push de acceso | P1; controles independientes | Flags triestado y posible mutación adicional | [Accesos](../../specs/access-control-and-users.md) |
| Usuarios, roles, dispositivos y modos permitidos | P1 lectura; P3 altas/bajas/cambios de derechos | Variantes legacy/recientes y comprobación de impacto | [Accesos](../../specs/access-control-and-users.md) |
| Acceso digital, PIN y credenciales de usuario | P3 o flujo oficial | Nunca como sensores/atributos; challenge específico | [Accesos](../../specs/access-control-and-users.md), [Administración](../../specs/protected-account-administration.md) |
| Alias de casa/dispositivos e idioma de contacto | P1; configuración explícita | Preservar unique_id y confirmar read-back | [Ajustes](../../specs/installation-and-device-settings.md) |
| Tiempos de entrada/salida y particiones | P1; `select`/`number` sólo con opciones reales | Lectura radio observada; rangos y esquema por panel | [Ajustes](../../specs/installation-and-device-settings.md) |
| Participación de sensores en total/día/noche | P1; configuración separada del armado | Editor/lectura observados; no convertir un checkbox en orden ARM | [Ajustes](../../specs/installation-and-device-settings.md) |
| Desactivación temporal de sensores | P3; flujo visible y con finalización | Reduce protección; nunca workaround automático | [Ajustes](../../specs/installation-and-device-settings.md) |
| Timbre, doorbell, volumen, sirena y lector | P1/P2; controles separados según hardware | Flags del lector/PIN protegidos; no una «sirena» universal | [Ajustes](../../specs/installation-and-device-settings.md) |
| Red actual, fuerza Wi-Fi y configuración de conexión | P1 lectura; P3 cambio de red | Consulta bajo demanda; secreto temporal y resultado ambiguo posible | [Ajustes](../../specs/installation-and-device-settings.md) |
| Wi-Fi sensing y capacidades de conectividad | P2; diagnóstico sólo con semántica demostrada | Nombre estático no demuestra detección de presencia ni telemetría | [Ajustes](../../specs/installation-and-device-settings.md) |
| Rutinas y programas de armado/desarmado | P1 lectura; P2 edición tipada | No duplicar scheduler remoto en HA; timezone/DST y permisos | [Rutinas](../../specs/provider-routines-and-schedules.md) |
| Recordatorios, ProtectMe y preavisos | P1/P2; calendario/eventos y administración explícita | Recordatorio no es orden de armado | [Rutinas](../../specs/provider-routines-and-schedules.md) |
| Vacaciones, periodos largos y agenda de cerradura/sensor | P2; calendario y gestión por capacidad | Separar contactos del plan y programa operativo | [Rutinas](../../specs/provider-routines-and-schedules.md) |
| Modo mascotas y reglas asociadas | P2; lectura/configuración si se verifica semántica | Contratos PetMode estáticos; no deducir bypass o alarma parcial | [Rutinas](../../specs/provider-routines-and-schedules.md) |
| Actividad, señales y exportaciones | P1; consulta privada paginada, eventos sin replay | Historial no es un flujo FCM ni un estado actual | [Actividad](../../specs/activity-inbox-and-incidents.md) |
| Buzón, contadores y preferencias de avisos | P1 contadores; P2 buzón; P3 leído/borrado/topics | Contadores GraphQL no contienen el buzón; RPC requiere transporte legítimo | [Actividad](../../specs/activity-inbox-and-incidents.md) |
| Saltos de alarma, incidencias e informes | Actual lista; P1/P2 detalles y consulta privada | Conservar reported/verified; no originar respuesta de emergencia | [Actividad](../../specs/activity-inbox-and-incidents.md) |
| Cámaras conectadas, galería y clips | P2; cámara y acceso privado a medios existentes | Autorización/familia, límites y transporte por validar | [Multimedia](../../specs/connected-camera-media.md) |
| Vídeo en directo, reproducción SD y eventos de cámara | P2; sesión multimedia bajo demanda | SDK nativo/codec/token; no ofrecer streaming de fotodetector por analogía | [Multimedia](../../specs/connected-camera-media.md) |
| Detección, privacidad, horario, SD, nombre y Wi-Fi de cámara | P2/P3; configuración admitida por modelo | Fuente estática; permisos de cámara separados de alarma | [Multimedia](../../specs/connected-camera-media.md) |
| Arlo, vincular cámara, formatear SD y borrar medios | Oficial para vinculación/destrucción; P2 lectura autorizada | OAuth/licencias, acciones irreversibles e identidad externa | [Multimedia](../../specs/connected-camera-media.md) |
| Cerradura: estado, cerrar/abrir y confirmación | P2; `lock` con capacidades reales | No inferir `open` de un contrato `lock:Boolean` | [Cerraduras](../../specs/smart-lock-management.md) |
| Autolock, ajustes, agenda y calibración | P2 ajustes/agenda; oficial calibración hasta procedimiento validado | Hardware Smartlock/Danalock y pasos físicos | [Cerraduras](../../specs/smart-lock-management.md) |
| Pilas, tamper, conectividad y revisiones | P1; diagnósticos y eventos con frescura | Alerta, porcentaje y salud completa son conceptos distintos | [Salud](../../specs/system-health-and-maintenance.md) |
| Confort, temperatura, humedad y entorno | P2; sensores sólo con fuente/unidad/timestamp verificados | Fuente ambiental no capturada; meteorología no mide la casa | [Salud](../../specs/system-health-and-maintenance.md) |
| Cambio guiado de pilas/DIY y suspensión de protección | P1 estado; P3 procedimiento manual controlado | Algunas queries tienen efectos; nunca polling rutinario | [Salud](../../specs/system-health-and-maintenance.md) |
| Envío de pilas, seguimiento, citas e informes de revisión | P1/P2 consulta; oficial pedidos/gestión no contratada | Direcciones y documentos privados; capacidad no equivale a cita reservada | [Salud](../../specs/system-health-and-maintenance.md) |
| Planes de acción, contactos y plan de vacaciones | P3; lectura/edición privada autorizada | Orden y ámbito instalación/persona; campos sensibles | [Administración](../../specs/protected-account-administration.md) |
| Perfil, teléfonos, password, palabra clave y coacción | P3 o flujo oficial | No publicar secretos ni convertirlos en entidades | [Administración](../../specs/protected-account-administration.md) |
| Terminales de confianza y acciones de alta seguridad | P3; observación y flujo autorizado específico | SMS/login no otorgan permiso global reutilizable | [Administración](../../specs/protected-account-administration.md) |
| Facturas, contrato y certificado de alarma | P3; documentos privados por petición, prioridad baja | Sin enlace público persistente ni descarga automática | [Administración](../../specs/protected-account-administration.md) |
| Tienda, pagos, cupones, titularidad, traslado y vinculación | Oficial; acceso a ruta humana si aporta valor | No automatizar contratación ni cambios jurídicos | [Administración](../../specs/protected-account-administration.md) |
| GDPR, campañas, valoraciones, analítica y validación de datos | Oficial; sin enviar telemetría de HA al SDK | Consentimientos y procesos de cuenta explícitos | [Administración](../../specs/protected-account-administration.md), [Base](../../specs/app-management-foundation.md) |
| Conéctame | P2; estado/configuración y eventos autorizados | UI nativa y contrato de lectura; setter/geofence SDK pendiente | [Servicios nativos](../../specs/personal-protection-and-native-services.md) |
| Guardián, SOS, Acompáñame y accidente | P2 observación legítima; oficial actuaciones de emergencia | Sensores/ubicación móvil, licencias y ámbito personal | [Servicios nativos](../../specs/personal-protection-and-native-services.md) |
| Familias, relojes, círculos, lugares e invitaciones | P2 lectura/presencia voluntaria; P3 administración futura | Identidad/consentimiento por persona, sin localización ficticia | [Servicios nativos](../../specs/personal-protection-and-native-services.md) |
| Voz, confirmación de armado, BASIC, tema y sesión local | Equivalentes HA donde proceda; resto oficial | No modificar preferencias del teléfono ni biometría desde Linux | [Servicios nativos](../../specs/personal-protection-and-native-services.md) |
| Chat, llamada, telemedicina, compartir, agenda y permisos SO | Oficial; enlaces humanos, sin llamadas/mensajes automáticos | Dependencias del dispositivo; no son sensores o acciones de alarma | [Servicios nativos](../../specs/personal-protection-and-native-services.md) |

## Contratos que condicionan la implementación

### Llaves y usuarios

`mkGetKeysRemotesList` devuelve recursos físicos con identidad, tipo, activación,
seguimiento y avisos; no basta con un alias. `UpdateKey` llama a `xSUpdateKey` y
su confirmación usa `GetKeyUpdStatus` → **`xSKeyupdStatus`**. El cliente también
declara `xSUpdateKeyTrackingStatus`: su uso depende de feature flags y panel.
Hay flags de diferencia **0 = conservar, 1 = activar, 2 = desactivar**, junto a
otros booleanos. No tratar todos como `bool` ni cambiar null por false.

Los campos de reasignación `oldUserId/newUserId`, usuarios legacy y usuarios
completos tienen contratos distintos. Una actualización física y el seguimiento
pueden confirmar por separado: el resultado parcial se conserva, sin rollback
que vuelva a conceder acceso. Los cambios de rol necesitan impacto visible y
autorización vigente. Estos detalles están trazados en ACCESS-1…ACCESS-8.

### Configuración y coste de las lecturas

Las consultas de panel, Wi-Fi y programa de sensor observadas iniciaban trabajo
remoto y consultaban su estado. No deben ejecutarse en cada actualización HA.
La lectura legacy de tiempos usa `entryTimeF/exitTimeF/entryTimeP/exitTimeP` y
el argumento `user` coincidió con el login en la consulta observada. Las
particiones recientes tienen otro esquema.

Los defaults estáticos FAST de entrada `[30,45,60]` y salida `[60,75,90,120]`, y
otra rama `[30,60,90,120]`, **no son rangos universales de valores aceptados**.
Antes de crear un `number` hay que resolver overrides y opciones del panel.
El programa de sensor usa TOTAL/PARTIALDAY/PARTIALNIGHT y la UI ARM_*: son
participaciones de configuración, no el estado armado ni el mapeo HA existente.
Wi-Fi sensing necesita establecer qué devuelve antes de proponer presencia.

### Rutinas y efectos ocultos

`UpdateAllSmartRoutines` llama a `xSUpdateStateSmartRoutine` con un identificador,
**sin argumento de estado deseado**. Su semántica no se validó en vivo: tratarlo
como no idempotente hasta comprobarla, con lectura fresca y sin retry ambiguo.
`LongTermPlan` selecciona tanto contactos como agenda: una vista calendario debe
pedir sólo lo necesario. `PetMode` precisa su propia semántica y elegibilidad.

El nombre GraphQL `query` **no demuestra ausencia de efectos**: operaciones como
`DIYInit` pueden iniciar un procedimiento que afecte a la protección. La política
de admisión debe clasificar la intención de negocio, no sólo query/mutation.

### Buzón, cámaras y protección personal

`NotificationsNotifier` devuelve categorías y contadores unread, no un historial
ni el texto del buzón. La app delega éste a `notifications.*`. FCM no permite
prometer reconstrucción completa durante una caída. Actividad, incidencia,
notificación y resultado verificado mantienen identidades y fechas separadas.

`xsCameras` declara streaming, eventos, SD y ajustes; GraphQL declara tokens y
autorización de cámaras/Arlo. Ninguno prueba por sí solo que un fotodetector sea
una cámara de vídeo o que Linux pueda llamar al SDK. `xSChangeSmartlockMode`
con `lock:Boolean` tampoco prueba una acción de apertura independiente.

Conéctame tiene lectura declarada y activación/desactivación en bridge nativo.
La ubicación de familias, relojes, Guardián y Acompáñame requiere servicio,
persona y consentimiento propios. El servidor HA no debe simular un teléfono,
GPS, biometría o sensor de accidente. `xSAllInOne`, que sólo selecciona res/msg,
no acredita una fuente de temperatura/humedad.

## Diseño recomendado y orden de ejecución

Diez SDDs Draft amplían las cinco baselines existentes. Todos tienen veinte
secciones, requisitos estables, aceptación, trazabilidad, límites operativos,
privacidad, recuperación, rollback y presupuesto de pruebas **futuro**.
El [catálogo](../../specs/CATALOG.md) y su [JSON](../../specs/catalog.json)
separan ambos estados; ninguna ruta de código o test propuesta se declara actual.

| Orden | Entrega vertical | Puerta de aceptación |
|---|---|---|
| 0 | [Base común de gestión](../../specs/app-management-foundation.md) | Capacidades/roles, acciones tipadas, admisión compartida, generaciones, privacidad, cancelación y no replay |
| 1 | Lectura de accesos, ajustes, actividad y salud | Contratos y permisos por panel; sin ampliar el polling normal |
| 2 | Alias y ajustes simples; después llaves/seguimiento | Mutación real, read-back, tipos, caducidad y resultado parcial comprobados |
| 3 | Rutinas y calendarios | Zona horaria/DST, concurrencia y operaciones no idempotentes resueltas |
| 4 | Cámaras conectadas y cerraduras | Hardware disponible, transporte/codec/autorización y semántica física probados |
| 5 | Administración protegida y servicios personales | UI privada, challenge por intención, consentimiento y límites del SDK resueltos |

La arquitectura conserva casos de uso y modelos independientes de HA; puertos
semánticos de dominio; mapeo GraphQL/SDK en adaptadores; composición por entrada;
y entidades/acciones HA como presentación. No se propone un servicio público
para ejecutar GraphQL/RPC arbitrarios, otra sesión global ni otro receptor FCM.
La identidad de entidades, UUID, opciones, sesión y polling de 1.1.0 se preservan.

Las familias nuevas estarán desactivadas inicialmente y se admitirán por capacidad
y permiso positivo. Las escrituras físicas comparten orden por instalación y
cooldown por origen; las operaciones lentas no retienen un permiso HTTP mientras
esperan. Priorizar la admisión de alarmas no significa poder cancelar una
configuración que el proveedor ya recibió.

La base común propone TTL de metadatos de cinco minutos y hasta doce consultas
de estado, separadas al menos cinco segundos y con plazo global de 65 segundos
para una operación radio. Son presupuestos iniciales de diseño por validar,
**no cuotas oficiales ni garantía de evitar bloqueos**. No se cambia el sondeo
actual de respaldo para introducir esta ampliación.

## Bloqueos y trabajo pendiente real

- Escrituras de llaves/usuarios: permiso y contrato por panel, flag del segundo
  paso, semántica de null/flags y confirmación real. No se ejecutaron para auditar.
- Ajustes: valores efectivos, particiones, audio/lector, deactivación y Wi-Fi
  sensing; los defaults públicos no sustituyen la capacidad concreta.
- Rutinas: semántica del cambio de estado, PetMode, timezone y aceptación legal.
- Buzón: API/SDK legítimo, esquema, paginación y confirmación de leído/borrado.
- Vídeo/SD/Arlo y cerradura: hardware, protocolo, permisos, límites y cierre de
  sesiones. No hubo prueba física de esos recursos en esta auditoría.
- Entorno: fuente autenticada de telemetría, unidad y fecha aún no capturadas.
- Administración y servicios personales: autorización reforzada y ámbito real;
  no inferir un permiso por tener sesión o un token push.

Los SDDs permanecen **Draft** hasta cerrar sus decisiones y revisar diseño,
aceptación y pruebas. Los presupuestos numéricos no son tests escritos ni
cobertura alcanzada. La futura implementación exigirá contratos sintéticos,
pruebas de errores/concurrencia/cancelación/aislamiento/privacidad y cobertura
total de nuevas políticas críticas y constructores de mutaciones. Las pruebas
físicas se separarán de CI y se limitarán al recurso y operación autorizados.

Esta auditoría no revalida la salud doméstica ni la cobertura de runtime de hoy.
La evidencia histórica de 1.1.0 sigue en [quality status](../quality-status.md).
Los controles de esta entrega son integridad documental, trazabilidad, inventario
y privacidad; sus resultados se registran junto al inventario.

## Fuentes primarias y conservación de evidencia

El inventario fija URLs y hashes del código público; el offset indicado es de
**caracteres**, no de bytes. No se incorpora el JavaScript completo ni se ejecuta
código descargado como parte del catálogo. Los extractos privados derivados
quedan fuera de Git para la posterior implementación; no se publica un HAR.

Las siguientes páginas se consultaron para contrastar familias de producto;
describen oferta general, no una garantía para la cuenta o el panel inspeccionado:

- [Configuración del sistema](https://www.verisure.es/cliente/configuracion-sistema),
  [datos del sistema](https://www.verisure.es/cliente/datos?panel=fast) y
  [dispositivos](https://www.verisure.es/cliente/dispositivos).
- [Usuarios y permisos de Smart Lock](https://www.verisure.es/smart-lock/usuarios-permisos).
- [Servicios](https://www.verisure.es/cliente/servicios),
  [protocolo de emergencia](https://www.verisure.es/cliente/protocolo-emergencia)
  y [uso de My Verisure](https://www.securitasdirect.es/alarmas/clientes/my-verisure-uso/).
- [FAQ oficial](https://www.verisure.es/consejos-y-ayuda/faqs),
  [manual digital 2026](https://www.verisure.es/sites/vs-es/files/flmngr/documentos/manuales_guias/Manualusuariodigital2026es.pdf)
  y [condiciones de la app](https://customers.verisure.es/media_contents/app/myverisure/android/terms_es_verisure.html).

La asignación de todas las firmas públicas a familias permite revisar de nuevo
una versión y detectar novedades sin confundir cantidad de documentos GraphQL
con cantidad de funcionalidades de producto.
