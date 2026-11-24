# Configuración de instalación, panel, sensores y red

- Status: Draft
- Date: 2026-11-24
- Catalog capability ID: installation-and-device-settings
- Last verified: 2026-11-24, investigación y diseño; implementación futura
- Owners: My Verisure maintainers
- Scope: alias, idioma, temporizadores, particiones, modos de sensor, sonidos y conectividad
- Required review gates: behavior, architecture, testing, documentation, security/operations
- Open decisions blocking readiness: variantes de panel/partición y rangos efectivos, confirmación de escrituras, flags MOK y chime/volumen por hardware; ausencia de contrato no habilita un control

## 1. Executive summary

Ofrecer configuración tipada con confirmación y con límites específicos del panel. Configurar en qué modos participa un sensor no es armarlo ni cambiar el mapeo Home/Night/Away de HA.

Se aplica íntegramente la [base común de gestión](app-management-foundation.md), especialmente permisos, admisión, privacidad, confirmación y aislamiento.

## 2. Problem, current behavior and evidence

Se observaron editor de tiempos, lectura Wi-Fi y modos de un fotodetector. Las lecturas de panel, red y programa de dispositivo iniciaban una solicitud y consultaban estados WAIT/OK. El menú y sus formularios se contrastaron con el nativo; no se guardaron valores.

La [auditoría](../docs/technical/2026-11-24-app-capability-audit.md) y el [inventario de operaciones](../docs/validation/2026-11-24-app-capabilities.json) separan fuente estática, UI nativa/web y consultas observadas. Este SDD no declara nuevas funciones instaladas.

## 3. Actors, surfaces and terminology

Tiempo de entrada/salida, participación de un sensor, desactivación temporal, timbre, volumen, sirena y armado actual son conceptos separados. Un SSID es dato de red; su contraseña es un secreto.

Actores: usuario HA autorizado, principal/rol Verisure, recurso de la cuenta o instalación y adaptadores HA/CLI. La visibilidad de un menú no otorga permisos de backend.

## 4. Goals, non-goals and fixed invariants

- SET-1 — **Capacidad concreta:** Derivar controles de panel, dispositivo, servicio y permiso reales; no asumir iguales flags o temporizadores en todas las instalaciones.
- SET-2 — **Tiempos por modo:** Leer y validar los cuatro tiempos legacy o las particiones admitidas; no convertir un rango general de segundos en valores universalmente válidos.
- SET-3 — **Participación del sensor:** Traducir TOTAL/PARTIALDAY/PARTIALNIGHT y ARM_TOTAL/ARM_DAY/ARM_NIGHT en el adaptador; preservar el total invariable del cliente y separar configuración de actuación.
- SET-4 — **Sonidos y flags:** Separar timbre por sensor, configuración de doorbell, volumen del panel y flags del lector; no presentar todos como una única sirena.
- SET-5 — **Red y secretos:** Consultar red y fuerza por sus contratos; configurar Wi-Fi requiere un flujo privado, sin password/SSID bruto en diagnósticos ni escaneos del servidor fingiendo ser el móvil.
- SET-6 — **Confirmación y suspensión:** Esperar el resultado autoritativo de cada escritura; tratar desactivaciones de sensores y mantenimiento como reducción de protección con límites y finalización explícitos.
- SET-7 — **Alias y concurrencia:** Preservar identidades al cambiar alias/idioma y detectar cambios concurrentes; no reenviar un formulario viejo al reiniciar.

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

| Área | Contratos | Precisión necesaria |
|---|---|---|
| Panel legacy | `xSGetPanelConfig`/`Status`, `xSUpdatePanelConfig`/`Status` | `entryTimeF/exitTimeF/entryTimeP/exitTimeP`; `user` coincide con el login en la lectura observada |
| Particiones | `xSGetAlarmPartitions`, `xSUpdateAlarmPartitions`/`Status` | esquema distinto; no reducir a cuatro campos sin evidencia |
| Sensor | `xSGetDeviceProgram`/`Status`, `xSUpdateDeviceProgram`/`Status` | respuesta usa TOTAL/PARTIALDAY/PARTIALNIGHT; UI usa ARM_* |
| Alias | `InstallationEdit`, `xSUpdateDevice`/`Status`, `UpdateCameraAlias` | resolver el identificador correcto de cada tipo |
| Timbre/lector | `UpdateChime`/`Status`, `xSGetDoorbellConfig`, `xSEditDoorbellConfig`/`Status`, `xSUpdMokSetting`/`Status` | flags y permisos por dispositivo |
| Audio | `xSUpdateSVKConfig`/`Status` | perfiles y dB del hardware, no sonido universal |
| Red | `xSGetConnectionConfig`, `xSGetWifiConnectionFast`/`Status`, `xSWifi*Strength*`, `xSUpdateWifi*Connection*` | lecturas radio y setters son operaciones diferentes |
| Wi-Fi sensing | `xSGetDeviceConfigsWifiSensing` | contrato estático: resolver campos, hardware y significado antes de ofrecer diagnóstico o presencia |
| Suspensión | `UpdateSensor`/`UpdateSensorStatus`, `DeactivationHistoryEligibility` | confirmar límites/impacto y fin de la suspensión; no es una lectura rutinaria |

El cliente inspeccionado define defaults FAST de entrada [30,45,60] y salida [60,75,90,120]; otra rama usa [30,60,90,120]. Son defaults de esas ramas, no una garantía de todos los paneles. Antes de implementar hay que resolver overrides y el contrato efectivo. Los flags/valores ausentes quedan unknown. La desactivación temporal de un sensor no se usa como mecanismo para evitar errores de armado.

Aplicar estados unknown/stale/pending/confirmed/partial/ambiguous según la base común. Un resultado antiguo, duplicado o cancelado no sustituye hechos más recientes.

## 7. User-facing configuration

Familia desactivada inicialmente. Proponer acciones independientes para alias, delays, programa de sensor, sonido y red; `select`/`number` de configuración sólo cuando se conozcan opciones efectivas. No ampliar el sondeo normal. Contraseña Wi-Fi: entrada secreta temporal; no restaurarla en formularios ni atributos.

## 8. Clean Architecture design

Puertos `InstallationSettingsRepository`, `SensorConfigurationRepository` y `NetworkConfigurationRepository`; modelos puros `PanelDelays`, `SensorParticipation`, `SoundProfile`, `NetworkObservation`. Futuros clientes por protocolo en `core/api/management/`; adaptadores HA separan acciones de configuración de `AlarmUseCase`. Pruebas AST impiden importar modelos de HA en el core.

Las rutas y tipos anteriores son propuestas. Reutilizar el grafo por entrada, las sesiones, el gate de proveedor y los mecanismos de publicación existentes. Extender el guardián de arquitectura y comprobar importaciones sin HA.

## 9. UI/UX and content contract

Mostrar tiempos por modo real del proveedor, equivalencia de configuración y antigüedad de lectura. «Conectando con el panel» es distinto de «Esperando guardado». Los controles inaccesibles explican su motivo. No reutilizar el botón armado total dentro de un editor de modos.

Etiquetas accesibles, localización y controles equivalentes en móvil/escritorio. Las acciones propuestas aún no existen en la versión instalada.

## 10. Failure, recovery and cleanup

Una lectura radio agotada conserva la configuración anterior con antigüedad; no aplica defaults al servidor. Si una red cambiada deja de responder, declarar resultado ambiguo y guiar al usuario, sin restaurar credenciales anteriores automáticamente. Un alias confirmado se conserva aunque falle otra fase.

Unload cancela seguimiento y drena persistencia; no equivale a deshacer la operación remota. Limpiar temporales propios conservando hechos confirmados y evidencia privada mínima.

## 11. Security, permissions and privacy

Las escrituras requieren administración y vínculo sesión/instalación vigente. Un flag del lector que modifica exigencia de PIN requiere tratamiento protegido. No desactivar protección en background ni guardar payloads privados de red o seriales en Recorder.

Se aplican controles de ámbito/rol vigentes y autorización explícita de automatizaciones de APP-6/7. Fixtures sintéticas; ningún secreto, dirección, identificador doméstico o captura HAR se incorpora al repositorio.

## 12. Observability and operations

Operaciones radio bajo demanda y con plazos; snapshots independientes del estado de alarma. No retener admisión HTTP durante esperas. Presupuesto común; las lecturas de fuerza Wi-Fi no corren en cada polling de HA.

Registrar duración, resultado y motivo local; sin mensajes arbitrarios del proveedor. Los presupuestos comunes son propuestas sujetas a medición, no límites oficiales.

## 13. Compatibility, migration, rollout and rollback

Habilitación por entrada y capacidad, primero lecturas, después escrituras manuales autorizadas. Preservar UUID, FCM, credenciales, unique_id y automatizaciones existentes. Eliminar/desactivar soporte local no modifica recursos remotos. Rollback mantiene snapshots privados versionados y deja las funciones incompatibles desactivadas.

## 14. Testing strategy and numeric budget

28 casos: siete riesgos por cuatro variantes, incluyendo límites exactos por panel, bool versus int, WAIT/OK/KO, configuración concurrente, red ambigua y secreto redactado.

Son mínimos propuestos para la futura implementación, no tests ya escritos ni cobertura medida. Usar relojes/repositorios/HTTP falsos y cero llamadas domésticas en CI; exigir 100% de líneas/rama en políticas críticas y constructores de mutaciones nuevos y respetar los gates del proyecto.

## 15. Documentation and discoverability

Mantener este SDD, [CATALOG.md](CATALOG.md), el inventario de operaciones y la auditoría. La futura implementación añadirá guía específica, acciones, permisos, migración y ejemplos con valores ficticios. No anunciar la capacidad como disponible antes de su aceptación.

## 16. Acceptance scenarios

| Requisito | Given / When / Then resumido |
|---|---|
| SET-1 | Dispositivo sin función de timbre; se descubre; no aparece un control ejecutable de timbre. |
| SET-2 | FAST recibe un tiempo no ofrecido por su contrato; el esquema lo rechaza antes de HTTP. |
| SET-3 | Se edita sólo participación nocturna; el armado actual no cambia y no se envía un comando ARM. |
| SET-4 | Hardware devuelve pinCode null; no se crea un switch que lo convierta en falso. |
| SET-5 | Se solicita cambio de red; hay fallo; no se registra la contraseña ni se repite el cambio. |
| SET-6 | Una operación devuelve referenceId; la UI sigue pendiente hasta confirmar, no muestra guardado inmediato. |
| SET-7 | Dos clientes cambian el alias; se detecta conflicto y se relee sin cambiar el unique_id. |

Cada escenario se descompone en variantes de tipos, autorización, error, concurrencia y recuperación según el presupuesto. La validación física requiere autorización concreta independiente.

## 17. Requirements traceability

| ID | Riesgo/función | Verificación futura | Responsable de implementación |
|---|---|---|---|
| SET-1 | Capacidad concreta | Caso de aceptación SET-1; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SET-2 | Tiempos por modo | Caso de aceptación SET-2; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SET-3 | Participación del sensor | Caso de aceptación SET-3; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SET-4 | Sonidos y flags | Caso de aceptación SET-4; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SET-5 | Red y secretos | Caso de aceptación SET-5; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SET-6 | Confirmación y suspensión | Caso de aceptación SET-6; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| SET-7 | Alias y concurrencia | Caso de aceptación SET-7; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |

Tests propuestos: `test_panel_configuration.py, test_sensor_configuration.py, test_network_configuration.py, test_device_settings_scope.py`. Son nombres de trabajo futuros, sin atribuirles ejecución actual. La evidencia disponible está en §2/6; los bloqueos del encabezado deben cerrarse antes de Ready for implementation.

## 18. Implementation or maintenance sequence

Revisar contratos y bloqueos → modelos/puertos semánticos → casos de uso con fakes → matriz de errores/privacidad → adaptador proveedor → presentación HA/CLI → compatibilidad/migración → lecturas controladas → escrituras concretas autorizadas cuando apliquen → rollout. No usar una prueba física peligrosa para completar una matriz sintética.

## 19. Definition of Done

- [ ] Requisitos y escenarios trazados; bloqueos de protocolo/permiso resueltos.
- [ ] Contratos por panel/hardware y confirmación comprobados.
- [ ] Tests, cobertura crítica, aislamiento, cancelación y privacidad verificados.
- [ ] Migración, rollback, guías y catálogo actualizados.
- [ ] Evidencia UI, sintética y física separadas, con sus límites publicados.

## 20. References and decisions

[Configuración oficial](https://www.verisure.es/cliente/configuracion-sistema) · [Datos de instalación actuales](installation-cameras-and-entity-identity.md) · [Administración protegida](protected-account-administration.md)

[Base común](app-management-foundation.md) · [Norma de SDDs](README.md) · [Decisión de dependencias](../docs/adr/0001-core-and-adapter-dependencies.md). Estado Draft: la elección de exposiciones HA es una recomendación de diseño, no un comportamiento observado del proveedor.
