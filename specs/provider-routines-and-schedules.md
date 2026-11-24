# Rutinas, programas, recordatorios y vacaciones del proveedor

- Status: Draft
- Date: 2026-11-24
- Catalog capability ID: provider-routines-and-schedules
- Last verified: 2026-11-24, investigación y diseño; implementación futura
- Owners: My Verisure maintainers
- Scope: automatizaciones almacenadas en Verisure, independientes de las automatizaciones locales de HA
- Required review gates: behavior, architecture, testing, documentation, security/operations
- Open decisions blocking readiness: zona horaria y reglas DST del backend, semántica de activación sin estado deseado, tipos de rutina por panel y confirmaciones; revisión de condiciones legales y programas ligados a cerraduras

## 1. Executive summary

Consultar y gestionar programas del proveedor con calendario, recurrencia y estado real. Preservar su ejecución remota cuando HA esté apagado y evitar duplicar la misma automatización en ambos sistemas.

Se aplica íntegramente la [base común de gestión](app-management-foundation.md), especialmente permisos, admisión, privacidad, confirmación y aislamiento.

## 2. Problem, current behavior and evidence

Los clientes muestran Rutinas; el buzón nativo anuncia esa evolución. Se observó la consulta resumida xSScheduler. Las operaciones detalladas, recordatorios, smart routines y planes largos están declaradas en el cliente, pero no se crearon ni activaron programas.

La [auditoría](../docs/technical/2026-11-24-app-capability-audit.md) y el [inventario de operaciones](../docs/validation/2026-11-24-app-capabilities.json) separan fuente estática, UI nativa/web y consultas observadas. Este SDD no declara nuevas funciones instaladas.

La segunda revisión abrió la lista nativa, onboarding (cancelado), formularios de
nueva rutina/nuevo aviso y ajuste de notificar sólo fallos. No se introdujeron
valores ni se guardó o activó ningún programa.

## 3. Actors, surfaces and terminology

Rutina, programa, recordatorio, suspensión de sensor, vacaciones y calendario HA no son sinónimos. El estado de un formulario no sustituye el campo active del recurso autoritativo.

Actores: usuario HA autorizado, principal/rol Verisure, recurso de la cuenta o instalación y adaptadores HA/CLI. La visibilidad de un menú no otorga permisos de backend.

## 4. Goals, non-goals and fixed invariants

- SCHED-1 — **Modelo completo:** Conservar tipo, acción, modo, fechas, hora, días, repetición, preaviso, expiración y estado; no inferir que existe un programa sólo porque aparece un indicador.
- SCHED-2 — **No idempotencia:** Un cambio de estado sin argumento desired-state se trata como no idempotente hasta validar su semántica; releer/serializar y no reenviar ante ambigüedad.
- SCHED-3 — **Tiempo y concurrencia:** Validar fechas, recurrencia, zona horaria y cambios de horario; detectar modificaciones externas antes de guardar.
- SCHED-4 — **Autoridad remota:** Distinguir rutinas del proveedor de automatizaciones HA; no copiarlas, activarlas o eliminarlas durante setup, migración o restauración.
- SCHED-5 — **Modos y permisos:** Validar modos y hardware permitidos; programas que armen total o actúen una puerta requieren intención explícita y quedan fuera de pruebas domésticas automáticas.
- SCHED-6 — **Vacaciones y privacidad:** Separar duración del plan, contactos de vacaciones y agenda de armado; no consultar contactos para una vista de calendario si no son necesarios.
- SCHED-7 — **Confirmación y legal:** Verificar creación/cambio/baja y respetar aceptación pendiente; no aceptar condiciones o convertir un recordatorio en una orden de armado.
- SCHED-8 — **Política de avisos:** Modelar «Notificar sólo en caso de fallo» separadamente del estado de cada rutina y de los filtros locales de HA; editarla sólo con ámbito y contrato confirmados, sin silenciar otros receptores por inferencia.

Las pruebas domésticas mantienen la prohibición de interior total. No se realizan compras, emergencias o actuaciones físicas por inferirlas de una notificación.

## 5. Current versus intended journey

```mermaid
flowchart LR
    A[Capacidad y permiso] --> B[Lectura o intención tipada]
    B --> C[Validar y confirmar]
    C --> D[Proyección HA con fecha]
    C --> E[Pendiente o requiere acción]
```

Equivalente: permiso del recurso → lectura/intención concreta → validación y confirmación → representación HA. Si falta contrato, permiso o resultado, no se publica un éxito. El estado actual es investigación; la implementación seguirá esta separación.

## 6. Functional behavior and state model

| Recurso | Referencias | Criterio |
|---|---|---|
| Resumen/lista | `xSScheduler`, `Scheduler`, `xSSmartRoutines` | el resumen id/active no contiene toda la definición |
| CRUD de programa | `AddScheduler`, `EditProgram`, `DelProgram` y estado de configuración | confirmar referencia y releer recurso |
| Recordatorio | `AddReminder`, `EditReminder`, `DelReminder`, `ProtectMe` | un aviso no es un armado |
| Estado de rutina | `UpdateAllSmartRoutines` → `xSUpdateStateSmartRoutine` | recibe smartRoutineId, sin estado deseado; no reintentar a ciegas |
| Periodos largos | `LongTermSchedule`, Add/Upd/DelLongTermSchedule | no filtrar contactos de LongTermPlan a calendario |
| Cerradura/sensor | `DoorlockScheduler`, `AddDoorlockScheduler`, `UpdateDoorlockScheduler`, `DelDoorlockProgram`, `DeviceScheduler` | requieren capacidad y semántica del dispositivo |
| Mascotas | `xSGetPetMode`, `xSCreatePetMode`, `xSUpdatePetMode` | contrato estático: elegibilidad, efecto, horario y confirmación pendientes; no asumir bypass ni activar por presencia |

Usar una representación de lectura y cambios tipados, sin conservar JSON arbitrario del backend. Mantener generación/versión del recurso; tras guardar, leer la definición vigente y comparar campos pretendidos. Si el proveedor sólo ofrece toggle, una petición set_enabled equivalente al estado actual es no-op después de una lectura fresca; su implementación queda bloqueada hasta verificar ese protocolo.

El modo mascotas pertenece a esta familia sólo si su semántica efectiva es de
programación/configuración. Si modifica participación o protección, aplicará
también SET-3/6 y el orden físico común. Debe verificarse sin inferir efectos a
partir del nombre; su creación/edición queda bloqueada hasta entonces.

Aplicar estados unknown/stale/pending/confirmed/partial/ambiguous según la base común. Un resultado antiguo, duplicado o cancelado no sustituye hechos más recientes.

La UI observada distingue sugerencias mañana/noche, rutinas existentes e intención
de crear, junto a Conéctame. Una tarjeta sugerida no es un programa activo. Los
formularios contienen nombre, hora, días individuales/atajos laborables-fin de
semana-todos, vigencia desde/hasta y duración indefinida. La rutina cambia a un
modo; el aviso comprueba si el modo **es distinto** de uno seleccionado. Conservar
esa condición en `RoutineChange`/`ReminderCondition`; no convertir el aviso en ARM.

El ajuste global de notificar sólo fallos se observó, pero no se capturó su setter
en el inventario GraphQL inicial. Investigar el módulo/transporte correspondiente
antes de exponer escritura. Un filtro de eventos HA no actualiza esa preferencia
del proveedor ni demuestra por sí solo recepción de avisos de ejecución.

## 7. User-facing configuration

Familia y escrituras desactivadas por defecto. Vista de agenda de sólo lectura; acciones propuestas list/configure/set_enabled/delete_routine con referencia opaca y tipo explícito. Formularios separados por programa, recordatorio y vacaciones. No introducir un toggle global que actúe todas las rutinas.

## 8. Clean Architecture design

Modelos `ProviderRoutine`, `Recurrence`, `RoutineChange`; puerto `SchedulingRepository`; política pura de fechas/concurrencia; cliente proveedor por variante legacy/smart. HA puede adaptar `calendar`, diagnósticos y acciones de administración; no usar su scheduler local para reproducir trabajos del proveedor.

Las rutas y tipos anteriores son propuestas. Reutilizar el grafo por entrada, las sesiones, el gate de proveedor y los mecanismos de publicación existentes. Extender el guardián de arquitectura y comprobar importaciones sin HA.

## 9. UI/UX and content contract

Identificar «Se ejecuta en Verisure», modo y próxima ocurrencia verificable. Mostrar definición y estado pendientes por separado. No afirmar una próxima fecha cuando la zona horaria o la regla no estén verificadas. Las bajas muestran el recurso exacto antes de su ejecución.

Etiquetas accesibles, localización y controles equivalentes en móvil/escritorio. Las acciones propuestas aún no existen en la versión instalada.

## 10. Failure, recovery and cleanup

Timeout tras crear: reconciliar por identidad/definición sin repetir ni crear otro ID. Si una fase cambia y otra falla, marcar parcial. Fallo de una automatización HA no cancela ni recrea programas remotos.

Unload cancela seguimiento y drena persistencia; no equivale a deshacer la operación remota. Limpiar temporales propios conservando hechos confirmados y evidencia privada mínima.

## 11. Security, permissions and privacy

Permisos administrativos y alcance por instalación. Las automatizaciones que gestionen programas necesitan lista explícita de acciones; no conceder permisos al recibir notificaciones. Contactos y aceptación legal quedan en sus flujos protegidos.

Se aplican controles de ámbito/rol vigentes y autorización explícita de automatizaciones de APP-6/7. Fixtures sintéticas; ningún secreto, dirección, identificador doméstico o captura HAR se incorpora al repositorio.

## 12. Observability and operations

Lectura bajo demanda o caché con fecha; agrupar avisos de cambios y consultar sólo la agenda afectada. No ejecutar un refresh por cada tick de calendario ni disparar acciones para comprobar un programa.

Registrar duración, resultado y motivo local; sin mensajes arbitrarios del proveedor. Los presupuestos comunes son propuestas sujetas a medición, no límites oficiales.

## 13. Compatibility, migration, rollout and rollback

Habilitación por entrada y capacidad, primero lecturas, después escrituras manuales autorizadas. Preservar UUID, FCM, credenciales, unique_id y automatizaciones existentes. Eliminar/desactivar soporte local no modifica recursos remotos. Rollback mantiene snapshots privados versionados y deja las funciones incompatibles desactivadas.

## 14. Testing strategy and numeric budget

32 casos: ocho riesgos por cuatro variantes; incluir dos transiciones DST,
no-op/toggle concurrente, envío ambiguo sin retry, vigencia, aviso condicionado
sin comando, privacidad de calendario y política de fallos separada del filtro HA.

Son mínimos propuestos para la futura implementación, no tests ya escritos ni cobertura medida. Usar relojes/repositorios/HTTP falsos y cero llamadas domésticas en CI; exigir 100% de líneas/rama en políticas críticas y constructores de mutaciones nuevos y respetar los gates del proyecto.

## 15. Documentation and discoverability

Mantener este SDD, [CATALOG.md](CATALOG.md), el inventario de operaciones y la auditoría. La futura implementación añadirá guía específica, acciones, permisos, migración y ejemplos con valores ficticios. No anunciar la capacidad como disponible antes de su aceptación.

## 16. Acceptance scenarios

| Requisito | Given / When / Then resumido |
|---|---|
| SCHED-1 | Programa sin fecha fin; se proyecta; no se confunde su vigencia con el interruptor activado. |
| SCHED-2 | Se pierde la respuesta a UpdateAllSmartRoutines; se reconcilia la lista sin enviar otra vez. |
| SCHED-3 | Una hora ambigua en cambio DST; se edita; se exige la interpretación contractual en lugar de elegir UTC silenciosamente. |
| SCHED-4 | HA reinicia con programas remotos existentes; no crea duplicados ni altera su estado. |
| SCHED-5 | Un test necesita simular modo total; usa repositorio falso y no contacta la instalación. |
| SCHED-6 | Se solicita sólo la agenda; no se usa la consulta mixta LongTermPlan que también devuelve contactos. |
| SCHED-7 | La respuesta exige condiciones; se devuelve acción requerida y no se activa el programa. |
| SCHED-8 | Se solicita cambiar sólo la política de avisos; contrato desconocido; se bloquea la escritura sin activar rutinas ni alterar los filtros FCM locales. |

Cada escenario se descompone en variantes de tipos, autorización, error, concurrencia y recuperación según el presupuesto. La validación física requiere autorización concreta independiente.

## 17. Requirements traceability

| ID | Riesgo/función | Verificación futura | Responsable de implementación |
|---|---|---|---|
| SCHED-1 | Modelo completo | Caso de aceptación SCHED-1; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-2 | No idempotencia | Caso de aceptación SCHED-2; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-3 | Tiempo y concurrencia | Caso de aceptación SCHED-3; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-4 | Autoridad remota | Caso de aceptación SCHED-4; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-5 | Modos y permisos | Caso de aceptación SCHED-5; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-6 | Vacaciones y privacidad | Caso de aceptación SCHED-6; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-7 | Confirmación y legal | Caso de aceptación SCHED-7; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SCHED-8 | Política de avisos | Caso de aceptación SCHED-8; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |

Tests propuestos: `test_provider_routines.py, test_routine_time_policy.py, test_routine_reconciliation.py, test_schedule_permissions.py`. Son nombres de trabajo futuros, sin atribuirles ejecución actual. La evidencia disponible está en §2/6; los bloqueos del encabezado deben cerrarse antes de Ready for implementation.

## 18. Implementation or maintenance sequence

Revisar contratos y bloqueos → modelos/puertos semánticos → casos de uso con fakes → matriz de errores/privacidad → adaptador proveedor → presentación HA/CLI → compatibilidad/migración → lecturas controladas → escrituras concretas autorizadas cuando apliquen → rollout. No usar una prueba física peligrosa para completar una matriz sintética.

## 19. Definition of Done

- [ ] Requisitos y escenarios trazados; bloqueos de protocolo/permiso resueltos.
- [ ] Contratos por panel/hardware y confirmación comprobados.
- [ ] Tests, cobertura crítica, aislamiento, cancelación y privacidad verificados.
- [ ] Migración, rollback, guías y catálogo actualizados.
- [ ] Evidencia UI, sintética y física separadas, con sus límites publicados.

## 20. References and decisions

[Programación oficial](https://www.verisure.es/cliente/configuracion-sistema) · [Modos de alarma](alarm-modes-and-confirmation.md) · [Planes protegidos](protected-account-administration.md)

[Base común](app-management-foundation.md) · [Norma de SDDs](README.md) · [Decisión de dependencias](../docs/adr/0001-core-and-adapter-dependencies.md). Estado Draft: la elección de exposiciones HA es una recomendación de diseño, no un comportamiento observado del proveedor.
