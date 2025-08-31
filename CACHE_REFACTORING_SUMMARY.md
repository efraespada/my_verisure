# Cache Refactoring Summary

## Overview
Se ha refactorizado la implementación del cache para seguir mejor los principios de responsabilidad única y arquitectura limpia. El cache se ha movido desde el `AlarmUseCaseImpl` al `InstallationUseCaseImpl`, que es donde realmente pertenece.

## Cambios Realizados

### 1. InstallationUseCaseImpl - Agregado Cache
- **Archivo**: `custom_components/my_verisure/use_cases/implementations/installation_use_case_impl.py`
- **Cambios**:
  - Agregada clase `InstallationInfoCache` para manejar el cache de servicios de instalación
  - Implementado cache con TTL configurable (por defecto 5 minutos)
  - Modificado `get_installation_services()` para usar cache automáticamente
  - Agregado soporte para `force_refresh` para bypassear el cache
  - Implementados métodos de gestión de cache: `clear_cache()`, `set_cache_ttl()`, `get_cache_info()`

### 2. AlarmUseCaseImpl - Simplificado
- **Archivo**: `custom_components/my_verisure/use_cases/implementations/alarm_use_case_impl.py`
- **Cambios**:
  - Eliminada clase `InstallationInfoCache` (movida a InstallationUseCase)
  - Eliminados métodos de gestión de cache específicos
  - Simplificado `_get_installation_info()` para usar directamente el `InstallationUseCase`
  - El cache ahora se maneja transparentemente a través del `InstallationUseCase`

### 3. Pruebas Actualizadas
- **Archivo**: `custom_components/my_verisure/tests/unit/use_cases/test_alarm_use_case.py`
- **Cambios**:
  - Agregado mock para `InstallationUseCase` en las pruebas
  - Actualizado fixture `alarm_use_case` para incluir ambas dependencias
  - Corregida creación de mock `InstallationServices` con parámetros requeridos

- **Archivo**: `custom_components/my_verisure/tests/unit/use_cases/test_installation_use_case.py`
- **Cambios**:
  - Agregadas nuevas pruebas específicas para el cache:
    - `test_get_installation_services_with_cache`: Verifica que el cache funciona
    - `test_get_installation_services_force_refresh`: Verifica que force_refresh bypassea el cache
    - `test_clear_cache`: Verifica limpieza de cache
    - `test_set_cache_ttl`: Verifica configuración de TTL
    - `test_get_cache_info`: Verifica información de cache

## Beneficios de la Refactorización

### 1. Responsabilidad Única
- El `InstallationUseCase` ahora es responsable de cachear sus propios datos
- El `AlarmUseCase` se enfoca únicamente en la lógica de alarmas

### 2. Reutilización
- El cache de servicios de instalación puede ser usado por otros casos de uso
- No hay duplicación de lógica de cache

### 3. Mantenibilidad
- El cache está centralizado en un solo lugar
- Más fácil de modificar y extender

### 4. Transparencia
- Los consumidores del `InstallationUseCase` obtienen cache automáticamente
- No necesitan preocuparse por la gestión del cache

## Funcionalidad del Cache

### Características
- **TTL configurable**: Por defecto 5 minutos, configurable via `set_cache_ttl()`
- **Cache por instalación**: Cada instalación tiene su propio cache independiente
- **Force refresh**: Opción para bypassear el cache cuando sea necesario
- **Gestión de cache**: Métodos para limpiar y obtener información del cache

### Uso
```python
# El cache se usa automáticamente
services = await installation_use_case.get_installation_services(installation_id)

# Para forzar refresh (bypassear cache)
services = await installation_use_case.get_installation_services(installation_id, force_refresh=True)

# Para limpiar cache
installation_use_case.clear_cache(installation_id)  # Cache específico
installation_use_case.clear_cache()  # Todo el cache

# Para configurar TTL
installation_use_case.set_cache_ttl(600)  # 10 minutos

# Para obtener información del cache
cache_info = installation_use_case.get_cache_info()
```

## Resultados de Pruebas
- ✅ Todas las pruebas de `AlarmUseCase` pasan (15/15)
- ✅ Todas las pruebas de `InstallationUseCase` pasan (12/12)
- ✅ Todas las pruebas de casos de uso pasan (37/37)

## Conclusión
La refactorización ha sido exitosa. El cache ahora está implementado en el lugar correcto (`InstallationUseCase`) y el `AlarmUseCase` es más simple y enfocado en su responsabilidad principal. La funcionalidad se mantiene intacta mientras se mejora la arquitectura del código.
