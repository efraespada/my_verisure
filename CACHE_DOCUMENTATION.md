# Caché de Installation Services

## Descripción

Se ha implementado un sistema de caché en memoria para la respuesta de `get_installation_services` que permite almacenar temporalmente la información de servicios de instalación para evitar llamadas repetidas a la API.

## Características

- **Caché en memoria**: Los datos se almacenan en memoria durante la sesión
- **TTL configurable**: Tiempo de vida del caché configurable (por defecto 5 minutos)
- **Invalidación automática**: El caché se limpia automáticamente al desconectar o hacer login
- **Invalidación manual**: Posibilidad de limpiar el caché manualmente
- **Force refresh**: Opción para forzar la actualización de datos ignorando el caché

## Métodos disponibles

### Gestión del caché

#### `get_installation_services(installation_id, force_refresh=False)`
Obtiene los servicios de instalación, usando caché si está disponible.

**Parámetros:**
- `installation_id` (str): ID de la instalación
- `force_refresh` (bool): Si es True, ignora el caché y obtiene datos frescos

**Retorna:**
- Dict con los datos de servicios de instalación

#### `clear_installation_services_cache(installation_id=None)`
Limpia el caché de servicios de instalación.

**Parámetros:**
- `installation_id` (str, opcional): ID específico de instalación a limpiar. Si es None, limpia todo el caché

#### `set_cache_ttl(ttl_seconds)`
Configura el tiempo de vida del caché en segundos.

**Parámetros:**
- `ttl_seconds` (int): Tiempo de vida en segundos

#### `get_cache_info()`
Obtiene información sobre el estado actual del caché.

**Retorna:**
- Dict con información del caché:
  - `cache_size`: Número de instalaciones en caché
  - `ttl_seconds`: TTL actual en segundos
  - `cached_installations`: Lista de IDs de instalaciones en caché
  - `cache_timestamps`: Información detallada de timestamps por instalación

## Ejemplo de uso

```python
from custom_components.my_verisure.api.client import MyVerisureClient

# Inicializar cliente
client = MyVerisureClient("username", "password")
await client.connect()
await client.login()

# Obtener instalaciones
installations = await client.get_installations()
installation_id = installations[0]["numinst"]

# Primera llamada - obtiene datos de la API y los cachea
services1 = await client.get_installation_services(installation_id)

# Segunda llamada - usa datos del caché (más rápido)
services2 = await client.get_installation_services(installation_id)

# Forzar actualización - ignora caché
services3 = await client.get_installation_services(installation_id, force_refresh=True)

# Cambiar TTL del caché
client.set_cache_ttl(60)  # 1 minuto

# Obtener información del caché
cache_info = client.get_cache_info()
print(f"Instalaciones en caché: {cache_info['cached_installations']}")

# Limpiar caché específico
client.clear_installation_services_cache(installation_id)

# Limpiar todo el caché
client.clear_installation_services_cache()
```

## Comportamiento automático

### Limpieza automática del caché

El caché se limpia automáticamente en los siguientes casos:

1. **Al hacer login**: Se limpia todo el caché al iniciar una nueva sesión
2. **Al desconectar**: Se limpia todo el caché al cerrar la conexión

### Validación del caché

El caché se considera válido si:
- Existe en memoria
- No ha expirado según el TTL configurado

## Ventajas

1. **Rendimiento**: Reduce llamadas a la API para datos que no cambian frecuentemente
2. **Eficiencia**: Mejora los tiempos de respuesta para llamadas repetidas
3. **Flexibilidad**: Permite control manual del caché cuando sea necesario
4. **Transparencia**: El caché es transparente para el código existente

## Consideraciones

1. **Memoria**: Los datos se almacenan en memoria, por lo que el uso de memoria aumentará con el número de instalaciones
2. **Actualización**: Los datos pueden estar desactualizados si cambian en el servidor antes de que expire el TTL
3. **Sesión**: El caché se pierde al reiniciar la aplicación o desconectar

## Configuración recomendada

- **TTL por defecto**: 5 minutos (300 segundos) - adecuado para la mayoría de casos
- **TTL corto**: 1-2 minutos para entornos donde los datos cambian frecuentemente
- **TTL largo**: 10-15 minutos para entornos estables con datos que cambian poco 