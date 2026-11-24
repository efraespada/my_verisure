# Estado, control y configuración de cerraduras inteligentes

- Status: Draft
- Date: 2026-11-24
- Catalog capability ID: smart-lock-management
- Last verified: 2026-11-24, investigación y diseño; implementación futura
- Owners: My Verisure maintainers
- Scope: cerraduras compatibles, su estado confirmado, configuración y relación explícita con alarmas
- Required review gates: behavior, architecture, testing, documentation, security/operations
- Open decisions blocking readiness: hardware de prueba por familia, enumeraciones y timestamps físicos, permisos, confirmación, autolock y efectos conjuntos con armado; no inferirlos de campos homónimos

## 1. Executive summary

Ofrecer una entidad lock sólo cuando exista cerradura y contrato confirmado. Bloquear, desbloquear y abrir son intenciones distintas; calibrar y configurar autolock requieren un flujo específico.

Se aplica íntegramente la [base común de gestión](app-management-foundation.md), especialmente permisos, admisión, privacidad, confirmación y aislamiento.

## 2. Problem, current behavior and evidence

El cliente contiene contratos Smartlock/Danalock, lectura de estado, cambio de modo, configuración, calibración y sus estados. La app oficial documenta apertura/cierre remotos y permisos. No se realizó ninguna actuación ni se verificó hardware de cerradura durante esta auditoría.

La [auditoría](../docs/technical/2026-11-24-app-capability-audit.md) y el [inventario de operaciones](../docs/validation/2026-11-24-app-capabilities.json) separan fuente estática, UI nativa/web y consultas observadas. Este SDD no declara nuevas funciones instaladas.

## 3. Actors, surfaces and terminology

Bloqueado, desbloqueado, puerta abierta, modo del motor y estado de la alarma son hechos diferentes. Autorizar a una persona para usar la app no es añadir un contacto para apertura por la central.

Actores: usuario HA autorizado, principal/rol Verisure, recurso de la cuenta o instalación y adaptadores HA/CLI. La visibilidad de un menú no otorga permisos de backend.

## 4. Goals, non-goals and fixed invariants

- LOCK-1 — **Descubrimiento:** Crear controles sólo para hardware/permiso positivos y conservar identidad por entrada y dispositivo.
- LOCK-2 — **Estado real:** Interpretar sólo enumeraciones verificadas; unknown/timeout no significan unlocked ni locked.
- LOCK-3 — **Acciones distintas:** Implementar lock/unlock/open únicamente si el contrato distingue esas acciones; nunca traducir open a un booleano suponiendo su significado.
- LOCK-4 — **Confirmación:** Enviar una intención una vez, comprobar referencia/estado/fecha y reconciliar ambigüedad sin repetir una apertura.
- LOCK-5 — **Configuración y calibración:** Separar autolock, modo, configuración y calibración; ésta requiere un procedimiento manual de hardware validado.
- LOCK-6 — **Composición explícita:** Armado y cerradura sólo se combinan con opción/intención y permisos independientes, preservando los mapeos existentes de alarma.
- LOCK-7 — **Ámbito y privacidad:** Comprobar autorización vigente, generación y dispositivo exacto; no registrar IDs/credenciales privados ni conceder acceso al desactivar una opción HA.

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

| Función | Referencia | Condición |
|---|---|---|
| Estado | `xSGetLockCurrentMode` | lockStatus/deviceId/statusTimestamp necesitan semántica por familia |
| Actuación | `xSChangeSmartlockMode`/`Status` | lock:Boolean no demuestra una acción open independiente |
| Configuración | Get/EditSmartlockConfig, Get/EditDanalockConfig y sus estados | adaptadores separados por generación |
| Autolock | configuración y `xSEditSmartlockAutolockStatus` | validar read-back y valores admitidos |
| Calibración | `xSCalibrateSmartlock`/`Status` | no test físico automático |
| Agenda | DoorlockScheduler | contrato del SDD de rutinas y permisos de lock |

Estado de operación: idle → enviando → pendiente → confirmado/ambiguo/fallido. El estado físico independiente sólo cambia con datos autoritativos. Una publicación tardía de estado no revierte un comando más reciente. Eliminar la entidad local no revoca usuarios ni desactiva autolock remoto.

Aplicar estados unknown/stale/pending/confirmed/partial/ambiguous según la base común. Un resultado antiguo, duplicado o cancelado no sustituye hechos más recientes.

## 7. User-facing configuration

Soporte opcional desactivado hasta validar hardware. Entidad lock; configuración en select/number/switch sólo con metadata conocida. Acciones manuales y automatizaciones autorizadas por separado. Calibración mediante flujo guiado oficial hasta completar su aceptación específica.

## 8. Clean Architecture design

Modelo `LockObservation`, `LockCommand`, `LockSettings`; puerto `SmartLockRepository` y clientes Smartlock/Danalock. Caso de uso compartido con CLI; HA lock adapter proyecta capacidades sin enum del proveedor. Compartir orden por instalación con comandos de alarma.

Las rutas y tipos anteriores son propuestas. Reutilizar el grafo por entrada, las sesiones, el gate de proveedor y los mecanismos de publicación existentes. Extender el guardián de arquitectura y comprobar importaciones sin HA.

## 9. UI/UX and content contract

«Cerradura bloqueada», «Estado desconocido» y «Apertura sin confirmar» con fecha de origen; no usar el color del panel de alarma como estado de puerta. Explicar cuándo una acción requiere presencia/procedimiento físico en la app.

Etiquetas accesibles, localización y controles equivalentes en móvil/escritorio. Las acciones propuestas aún no existen en la versión instalada.

## 10. Failure, recovery and cleanup

Ante motor/error o respuesta ambigua, no hacer rollback físico ni alternar el booleano para intentar recuperar. Cancelar seguimiento local conserva la incertidumbre y exige una lectura posterior autorizada.

Unload cancela seguimiento y drena persistencia; no equivale a deshacer la operación remota. Limpiar temporales propios conservando hechos confirmados y evidencia privada mínima.

## 11. Security, permissions and privacy

Permisos de puerta separados de alarma y usuarios. No efectuar aperturas por cualquier push. Las pruebas físicas exigen autorización concreta, condiciones de seguridad del propietario y restauración acordada; nunca se incluyen en CI.

Se aplican controles de ámbito/rol vigentes y autorización explícita de automatizaciones de APP-6/7. Fixtures sintéticas; ningún secreto, dirección, identificador doméstico o captura HAR se incorpora al repositorio.

## 12. Observability and operations

Estado bajo demanda/push verificado cuando exista; agrupación y presupuesto común. Evitar consultas continuas al motor o sondeos por cada notificación de cuenta.

Registrar duración, resultado y motivo local; sin mensajes arbitrarios del proveedor. Los presupuestos comunes son propuestas sujetas a medición, no límites oficiales.

## 13. Compatibility, migration, rollout and rollback

Habilitación por entrada y capacidad, primero lecturas, después escrituras manuales autorizadas. Preservar UUID, FCM, credenciales, unique_id y automatizaciones existentes. Eliminar/desactivar soporte local no modifica recursos remotos. Rollback mantiene snapshots privados versionados y deja las funciones incompatibles desactivadas.

## 14. Testing strategy and numeric budget

28 casos: siete riesgos por cuatro variantes, incluyendo estado desconocido, open no soportado, comando ambiguo, actor sin permiso y carreras entre alarma/cerradura.

Son mínimos propuestos para la futura implementación, no tests ya escritos ni cobertura medida. Usar relojes/repositorios/HTTP falsos y cero llamadas domésticas en CI; exigir 100% de líneas/rama en políticas críticas y constructores de mutaciones nuevos y respetar los gates del proyecto.

## 15. Documentation and discoverability

Mantener este SDD, [CATALOG.md](CATALOG.md), el inventario de operaciones y la auditoría. La futura implementación añadirá guía específica, acciones, permisos, migración y ejemplos con valores ficticios. No anunciar la capacidad como disponible antes de su aceptación.

## 16. Acceptance scenarios

| Requisito | Given / When / Then resumido |
|---|---|
| LOCK-1 | La instalación no tiene cerradura; no aparece un lock ficticio. |
| LOCK-2 | El proveedor devuelve un código nuevo; HA muestra estado desconocido sin acciones derivadas. |
| LOCK-3 | Sólo se conoce lock:Boolean; open no se anuncia como soportado. |
| LOCK-4 | Se pierde la respuesta de unlock; no se vuelve a enviar para obtener un OK. |
| LOCK-5 | HA reinicia; no calibra ni hace girar el motor durante descubrimiento. |
| LOCK-6 | Se arma Night sin opción de cerradura; no se ejecuta ninguna actuación de puerta. |
| LOCK-7 | Una entrada intenta operar la cerradura de otra; se rechaza antes de HTTP. |

Cada escenario se descompone en variantes de tipos, autorización, error, concurrencia y recuperación según el presupuesto. La validación física requiere autorización concreta independiente.

## 17. Requirements traceability

| ID | Riesgo/función | Verificación futura | Responsable de implementación |
|---|---|---|---|
| LOCK-1 | Descubrimiento | Caso de aceptación LOCK-1; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| LOCK-2 | Estado real | Caso de aceptación LOCK-2; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| LOCK-3 | Acciones distintas | Caso de aceptación LOCK-3; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| LOCK-4 | Confirmación | Caso de aceptación LOCK-4; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| LOCK-5 | Configuración y calibración | Caso de aceptación LOCK-5; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| LOCK-6 | Composición explícita | Caso de aceptación LOCK-6; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| LOCK-7 | Ámbito y privacidad | Caso de aceptación LOCK-7; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |

Tests propuestos: `test_smartlock_contracts.py, test_lock_state_mapping.py, test_lock_command_ordering.py, test_lock_permissions.py`. Son nombres de trabajo futuros, sin atribuirles ejecución actual. La evidencia disponible está en §2/6; los bloqueos del encabezado deben cerrarse antes de Ready for implementation.

## 18. Implementation or maintenance sequence

Revisar contratos y bloqueos → modelos/puertos semánticos → casos de uso con fakes → matriz de errores/privacidad → adaptador proveedor → presentación HA/CLI → compatibilidad/migración → lecturas controladas → escrituras concretas autorizadas cuando apliquen → rollout. No usar una prueba física peligrosa para completar una matriz sintética.

## 19. Definition of Done

- [ ] Requisitos y escenarios trazados; bloqueos de protocolo/permiso resueltos.
- [ ] Contratos por panel/hardware y confirmación comprobados.
- [ ] Tests, cobertura crítica, aislamiento, cancelación y privacidad verificados.
- [ ] Migración, rollback, guías y catálogo actualizados.
- [ ] Evidencia UI, sintética y física separadas, con sus límites publicados.

## 20. References and decisions

[Usuarios y permisos de cerradura](https://www.verisure.es/smart-lock/usuarios-permisos) · [Rutinas](provider-routines-and-schedules.md) · [Modos existentes](alarm-modes-and-confirmation.md)

[Base común](app-management-foundation.md) · [Norma de SDDs](README.md) · [Decisión de dependencias](../docs/adr/0001-core-and-adapter-dependencies.md). Estado Draft: la elección de exposiciones HA es una recomendación de diseño, no un comportamiento observado del proveedor.
