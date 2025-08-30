# Refactorización del Client.py

## Resumen

El archivo `client.py` original tenía más de 2300 líneas y era difícil de mantener. Se ha refactorizado dividiéndolo en módulos especializados siguiendo el principio de responsabilidad única.

## Nueva Arquitectura

### 1. Base Client (`base_client.py`)
- **Responsabilidad**: Funcionalidad común de HTTP y GraphQL
- **Funciones**:
  - Conexión HTTP básica
  - Headers y cookies
  - Ejecución de queries GraphQL
  - Gestión de sesiones HTTP

### 2. Device Manager (`device_manager.py`)
- **Responsabilidad**: Gestión de identificadores de dispositivos
- **Funciones**:
  - Generación de UUIDs de dispositivo
  - Persistencia de identificadores
  - Variables para login y validación

### 3. Auth Client (`auth_client.py`)
- **Responsabilidad**: Autenticación y OTP
- **Funciones**:
  - Login inicial
  - Device authorization
  - Manejo de OTP (enviar/verificar)
  - Gestión de tokens de autenticación

### 4. Session Client (`session_client.py`)
- **Responsabilidad**: Gestión de sesiones
- **Funciones**:
  - Guardar/cargar sesiones
  - Validación de sesiones
  - Gestión de cookies
  - Conversión a DTOs

### 5. Installation Client (`installation_client.py`)
- **Responsabilidad**: Gestión de instalaciones
- **Funciones**:
  - Obtener lista de instalaciones
  - Obtener servicios de instalación
  - Cache de servicios
  - Gestión de TTL

### 6. Alarm Client (`alarm_client.py`)
- **Responsabilidad**: Control de alarmas
- **Funciones**:
  - Estado de alarmas
  - Armado/desarmado
  - Polling de estado
  - Procesamiento de mensajes

### 7. Client Refactorizado (`client_refactored.py`)
- **Responsabilidad**: Orquestación de todos los módulos
- **Funciones**:
  - Interfaz unificada
  - Gestión de estado interno
  - Compatibilidad con código existente

## Ventajas de la Refactorización

### 1. **Mantenibilidad**
- Cada módulo tiene una responsabilidad específica
- Código más fácil de entender y modificar
- Menor acoplamiento entre funcionalidades

### 2. **Testabilidad**
- Cada módulo puede ser testeado independientemente
- Mocks más específicos
- Tests más enfocados

### 3. **Reutilización**
- Módulos pueden ser reutilizados en otros contextos
- Fácil extensión de funcionalidades
- Separación clara de responsabilidades

### 4. **Escalabilidad**
- Nuevos módulos pueden ser añadidos fácilmente
- Modificaciones aisladas
- Arquitectura más modular

## Estructura de Archivos

```
api/
├── base_client.py          # Cliente base con funcionalidad HTTP/GraphQL
├── device_manager.py       # Gestión de dispositivos
├── auth_client.py          # Autenticación y OTP
├── session_client.py       # Gestión de sesiones
├── installation_client.py  # Gestión de instalaciones
├── alarm_client.py         # Control de alarmas
├── client_refactored.py    # Cliente principal refactorizado
├── client.py              # Cliente original (mantener para compatibilidad)
├── models/                # DTOs y modelos de dominio
│   ├── dto/
│   └── domain/
├── fields.py              # Constantes y campos
└── exceptions.py          # Excepciones personalizadas
```

## Migración

### Para usar el cliente refactorizado:

```python
from api.client_refactored import MyVerisureClientRefactored

# Uso similar al cliente original
client = MyVerisureClientRefactored(user, password)
await client.connect()

# Login
auth_result = await client.login()

# Obtener instalaciones
installations = await client.get_installations()

# Control de alarmas
await client.arm_alarm_away(installation_id)
```

### Compatibilidad

El cliente refactorizado mantiene la misma interfaz pública que el original, por lo que la migración es transparente.

## Próximos Pasos

1. **Tests**: Crear tests unitarios para cada módulo
2. **Documentación**: Documentar cada módulo individualmente
3. **Migración gradual**: Migrar componentes uno por uno
4. **Optimización**: Optimizar cada módulo según sus necesidades específicas

## Beneficios Esperados

- **Reducción de bugs**: Código más específico y testeable
- **Desarrollo más rápido**: Módulos independientes
- **Mejor rendimiento**: Optimizaciones específicas por módulo
- **Facilidad de mantenimiento**: Cambios aislados y controlados 