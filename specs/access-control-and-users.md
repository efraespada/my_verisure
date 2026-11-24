# Llaves, mandos, usuarios y permisos de acceso

- Status: Draft
- Date: 2026-11-24
- Catalog capability ID: access-control-and-users
- Last verified: 2026-11-24, investigación y diseño; implementación futura
- Owners: My Verisure maintainers
- Scope: dispositivos físicos de acceso y usuarios asociados a una instalación
- Required review gates: behavior, architecture, testing, documentation, security/operations
- Open decisions blocking readiness: capturar escrituras reversibles autorizadas en cada panel; resolver el flag de seguimiento separado, nulabilidad, reasignación y permisos de usuarios; confirmar costes si un flujo ofrece una llave nueva

## 1. Executive summary

Consultar y gestionar llaves/mandos y usuarios mediante intenciones explícitas y confirmadas. Separar el dispositivo físico, su usuario asignado, el acceso digital y sus permisos; una llave inactiva no es un usuario eliminado.

Se aplica íntegramente la [base común de gestión](app-management-foundation.md), especialmente permisos, admisión, privacidad, confirmación y aislamiento.

## 2. Problem, current behavior and evidence

Se abrieron la lista y el editor de una llave en Chrome y en el WebView nativo: nombre, habilitación, seguimiento y avisos por email/push coincidían. Se observaron lecturas de llaves y usuarios secundarios; ninguna escritura. El cliente contiene variantes por panel y feature flag para actualización y seguimiento.

La [auditoría](../docs/technical/2026-11-24-app-capability-audit.md) y el [inventario de operaciones](../docs/validation/2026-11-24-app-capabilities.json) separan fuente estática, UI nativa/web y consultas observadas. Este SDD no declara nuevas funciones instaladas.

## 3. Actors, surfaces and terminology

Llave/mando, slot físico, usuario de instalación, usuario digital, rol, permiso de modo y seguimiento son objetos diferentes. Las referencias locales no contienen DNI, seriales ni IDs del proveedor.

Actores: usuario HA autorizado, principal/rol Verisure, recurso de la cuenta o instalación y adaptadores HA/CLI. La visibilidad de un menú no otorga permisos de backend.

## 4. Goals, non-goals and fixed invariants

- ACCESS-1 — **Identidad y lectura:** Listar sólo recursos de la entrada y conservar IDs HA aunque cambien alias u orden; activación, seguimiento y avisos desconocidos permanecen desconocidos.
- ACCESS-2 — **Intención de acceso:** Activar/desactivar o reasignar exige permiso positivo, selección inequívoca y una intención explícita; no activar slots ni autorizar usuarios por descubrimiento.
- ACCESS-3 — **Patch y confirmación:** Construir el cambio sobre una lectura vigente; preservar campos ajenos y traducir los flags triestado nativos 0/1/2 sólo en el adaptador; publicar tras confirmación/lectura posterior.
- ACCESS-4 — **Seguimiento independiente:** Mantener separados seguimiento, email y push; no forzar false ante null ni asumir que todas las versiones usan una sola mutación.
- ACCESS-5 — **Usuarios y roles:** Aplicar restricciones de titular/administrador/restringido/mínimo y modos permitidos según el proveedor; alta, baja y reasignación no aceptan IDs externos ni degradan al titular a ciegas.
- ACCESS-6 — **Acciones protegidas:** La creación de acceso digital y los cambios de PIN/contraseña se derivan al flujo protegido; no publicar secretos ni aceptar confirmaciones genéricas reutilizables.
- ACCESS-7 — **Privacidad:** Exponer alias elegidos y estado permitido; reservar roster, contactos, seriales e identificadores a respuestas privadas autorizadas, sin atributos ni trazas libres.
- ACCESS-8 — **Orden y recuperación:** Serializar por instalación y recurso; ante timeout o reinicio reconciliar sin repetir activaciones, bajas o cambios de rol.

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

| Función | Referencia del cliente | Condición |
|---|---|---|
| Inventario | `mkGetKeysRemotesList` → `xSKeys.keysList` | `ident/lix/lixCu`, tipo, activación y flags no son intercambiables |
| Edición física/alias | `UpdateKey` → `xSUpdateKey`, `GetKeyUpdStatus` → `xSKeyupdStatus` | input propio del panel y confirmación por referencia |
| Seguimiento | `xSUpdateKeyTrackingStatus` | flujo separado condicionado por feature flag; confirmar cuándo aplica |
| Usuarios legacy | `mkSecondUsers`, `mkAddSecondUser`, `DeleteSecondUser` | difiere de usuarios completos de paneles recientes |
| Usuarios y permisos | `mkUsers`, `mkEditUser`, `xSUpdateArmModesPermissions`, `xSUpdateUserDevices` y sus estados | no extrapolar permisos a partir de etiquetas traducidas |
| Reasignación | campos `oldUserId/newUserId`, listas de usuarios autorizados | confirmar soporte por panel y evitar asignaciones ajenas |

El editor nativo usa diferencias triestado para algunos flags, booleanos para otros y conserva campos físicos al actualizar. Validar tipos, ausencia/null y correspondencia del slot; nunca construir un input parcial inventado. Una baja de usuario puede cambiar derechos asociados: mostrar impacto antes de la acción. Una nueva llave física o compra se tramita fuera de automatizaciones HA.

Aplicar estados unknown/stale/pending/confirmed/partial/ambiguous según la base común. Un resultado antiguo, duplicado o cancelado no sustituye hechos más recientes.

## 7. User-facing configuration

Familia de acceso desactivada por defecto. Lectura bajo demanda; entidades de configuración opcionales por recurso. Acciones propuestas: `my_verisure.list_access_keys`, `configure_access_key`, `list_installation_users` y flujos específicos de usuario. Alias: cadena no vacía, sin controles, con longitud máxima contractual verificada; booleanos estrictos. No ofrecer un campo libre `input` del proveedor.

## 8. Clean Architecture design

Modelos `AccessKey`, `InstallationUser`, `AccessChange` y puertos `AccessRepository`/`UserAdministration`; futuros adaptadores `core/api/management/access_client.py` y `access_mapper.py`. Casos de uso de listar, modificar y reconciliar; HA proyecta switches de configuración sólo donde exista permiso/contrato. La política triestado permanece fuera de entidades HA.

Las rutas y tipos anteriores son propuestas. Reutilizar el grafo por entrada, las sesiones, el gate de proveedor y los mecanismos de publicación existentes. Extender el guardián de arquitectura y comprobar importaciones sin HA.

## 9. UI/UX and content contract

Mostrar «Llave habilitada», «Estado desconocido», «Cambio pendiente» y los campos realmente guardados si hay resultado parcial. Antes de una baja/reasignación, identificar el recurso y el efecto; nunca un botón ambiguo con icono sin etiqueta. No presentar un selector de usuarios si el panel sólo admite slots legacy.

Etiquetas accesibles, localización y controles equivalentes en móvil/escritorio. Las acciones propuestas aún no existen en la versión instalada.

## 10. Failure, recovery and cleanup

Si la fase física termina y el seguimiento falla, conservar el resultado físico y refrescar únicamente el recurso afectado. No reactivar una llave como rollback. En conflicto entre snapshot y edición, invalidar el formulario y volver a leer, sin sobrescribir campos concurrentes.

Unload cancela seguimiento y drena persistencia; no equivale a deshacer la operación remota. Limpiar temporales propios conservando hechos confirmados y evidencia privada mínima.

## 11. Security, permissions and privacy

Los permisos efectivos se comprueban tras renovar sesión y antes de enviar. Las automatizaciones necesitan autorización acotada para la acción concreta; no heredan privilegios por ausencia de usuario. No mostrar PIN, contraseñas o documentos personales en nombres de entidades.

Se aplican controles de ámbito/rol vigentes y autorización explícita de automatizaciones de APP-6/7. Fixtures sintéticas; ningún secreto, dirección, identificador doméstico o captura HAR se incorpora al repositorio.

## 12. Observability and operations

Sin sondeo de radio por llave en cada actualización de alarma. La lista puede usar caché marcada; toda escritura usa hechos vigentes. Agrupar refreshes concurrentes de la lista y respetar el presupuesto común de confirmación.

Registrar duración, resultado y motivo local; sin mensajes arbitrarios del proveedor. Los presupuestos comunes son propuestas sujetas a medición, no límites oficiales.

## 13. Compatibility, migration, rollout and rollback

Habilitación por entrada y capacidad, primero lecturas, después escrituras manuales autorizadas. Preservar UUID, FCM, credenciales, unique_id y automatizaciones existentes. Eliminar/desactivar soporte local no modifica recursos remotos. Rollback mantiene snapshots privados versionados y deja las funciones incompatibles desactivadas.

## 14. Testing strategy and numeric budget

32 casos: ocho reglas de riesgo con cuatro variantes cada una (válida, no permitida/desconocida, fallo parcial/timeout, aislamiento o reinicio). Añadir matrices de panel/flag sin duplicar casos triviales.

Son mínimos propuestos para la futura implementación, no tests ya escritos ni cobertura medida. Usar relojes/repositorios/HTTP falsos y cero llamadas domésticas en CI; exigir 100% de líneas/rama en políticas críticas y constructores de mutaciones nuevos y respetar los gates del proyecto.

## 15. Documentation and discoverability

Mantener este SDD, [CATALOG.md](CATALOG.md), el inventario de operaciones y la auditoría. La futura implementación añadirá guía específica, acciones, permisos, migración y ejemplos con valores ficticios. No anunciar la capacidad como disponible antes de su aceptación.

## 16. Acceptance scenarios

| Requisito | Given / When / Then resumido |
|---|---|
| ACCESS-1 | Lista reordenada y alias cambiado; se refresca; las referencias y automatizaciones existentes se conservan. |
| ACCESS-2 | Llave nueva/inactiva descubierta; se inicia HA; no se envía activación ni se concede acceso. |
| ACCESS-3 | Sólo cambia el alias; se guarda; los permisos y avisos conservan sus valores y un acuse sin confirmación deja pendiente. |
| ACCESS-4 | Actualización física confirmada y fase de seguimiento fallida; se informa resultado parcial sin revertir acceso automáticamente. |
| ACCESS-5 | Usuario restringido intenta conceder privilegios; el caso de uso rechaza antes del envío. |
| ACCESS-6 | La sesión existe pero falta autorización adicional; se solicita el paso protegido sin repetir la escritura. |
| ACCESS-7 | Respuesta incluye teléfono y serial; se proyecta una entidad; esos datos no aparecen en estados ni diagnósticos. |
| ACCESS-8 | La respuesta se pierde tras enviar; se vuelve a abrir HA; no se reenvía la mutación. |

Cada escenario se descompone en variantes de tipos, autorización, error, concurrencia y recuperación según el presupuesto. La validación física requiere autorización concreta independiente.

## 17. Requirements traceability

| ID | Riesgo/función | Verificación futura | Responsable de implementación |
|---|---|---|---|
| ACCESS-1 | Identidad y lectura | Caso de aceptación ACCESS-1; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-2 | Intención de acceso | Caso de aceptación ACCESS-2; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-3 | Patch y confirmación | Caso de aceptación ACCESS-3; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-4 | Seguimiento independiente | Caso de aceptación ACCESS-4; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-5 | Usuarios y roles | Caso de aceptación ACCESS-5; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-6 | Acciones protegidas | Caso de aceptación ACCESS-6; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-7 | Privacidad | Caso de aceptación ACCESS-7; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |
| ACCESS-8 | Orden y recuperación | Caso de aceptación ACCESS-8; matriz sintética de §14 | Política/caso de uso y adaptador descritos en §8 |

Tests propuestos: `test_access_contracts.py, test_access_patches.py, test_access_permissions.py, test_access_recovery.py`. Son nombres de trabajo futuros, sin atribuirles ejecución actual. La evidencia disponible está en §2/6; los bloqueos del encabezado deben cerrarse antes de Ready for implementation.

## 18. Implementation or maintenance sequence

Revisar contratos y bloqueos → modelos/puertos semánticos → casos de uso con fakes → matriz de errores/privacidad → adaptador proveedor → presentación HA/CLI → compatibilidad/migración → lecturas controladas → escrituras concretas autorizadas cuando apliquen → rollout. No usar una prueba física peligrosa para completar una matriz sintética.

## 19. Definition of Done

- [ ] Requisitos y escenarios trazados; bloqueos de protocolo/permiso resueltos.
- [ ] Contratos por panel/hardware y confirmación comprobados.
- [ ] Tests, cobertura crítica, aislamiento, cancelación y privacidad verificados.
- [ ] Migración, rollback, guías y catálogo actualizados.
- [ ] Evidencia UI, sintética y física separadas, con sus límites publicados.

## 20. References and decisions

[Gestión oficial de datos y usuarios](https://www.verisure.es/cliente/datos?panel=fast) · [Llaves y permisos](https://www.verisure.es/smart-lock/usuarios-permisos) · [Acciones protegidas](protected-account-administration.md)

[Base común](app-management-foundation.md) · [Norma de SDDs](README.md) · [Decisión de dependencias](../docs/adr/0001-core-and-adapter-dependencies.md). Estado Draft: la elección de exposiciones HA es una recomendación de diseño, no un comportamiento observado del proveedor.
