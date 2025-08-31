# My Verisure CLI

Command Line Interface para la integración de My Verisure, construido sobre la misma arquitectura que usa Home Assistant.

## Características

- ✅ **Reutilización total del código**: Usa exactamente los mismos casos de uso que Home Assistant
- ✅ **Flujo OTP completo**: Maneja automáticamente la verificación de dispositivos
- ✅ **Modos de operación**: Interactivo, no interactivo y batch
- ✅ **Gestión de sesión persistente**: Mantiene la autenticación entre comandos usando archivos
- ✅ **Arquitectura modular**: Comandos independientes y reutilizables

## Instalación

El CLI está incluido en el repositorio. Para usarlo:

```bash
# Ejecutar directamente
python my_verisure_cli.py [comando] [opciones]

# O hacer un enlace simbólico para usar como comando
ln -s $(pwd)/my_verisure_cli.py /usr/local/bin/my_verisure
my_verisure [comando] [opciones]
```

## Comandos Disponibles

### Autenticación

```bash
# Iniciar sesión (interactivo)
my_verisure auth login

# Cerrar sesión
my_verisure auth logout

# Ver estado de autenticación
my_verisure auth status
```

### Información

```bash
# Listar todas las instalaciones
my_verisure info installations

# Ver servicios de una instalación específica
my_verisure info services --installation-id 12345

# Ver estado de una instalación
my_verisure info status --installation-id 12345
```

### Control de Alarmas

```bash
# Ver estado de la alarma
my_verisure alarm status --installation-id 12345

# Armar alarma en modo away
my_verisure alarm arm --mode away --installation-id 12345

# Armar alarma en modo home
my_verisure alarm arm --mode home --installation-id 12345

# Armar alarma en modo night
my_verisure alarm arm --mode night --installation-id 12345

# Desarmar alarma
my_verisure alarm disarm --installation-id 12345
```

## Modos de Operación

### Modo Interactivo (Por defecto)

El CLI guía al usuario paso a paso:

```bash
my_verisure auth login
# Solicita credenciales
# Si requiere OTP, muestra teléfonos disponibles
# Solicita código OTP
# Completa la autenticación
```

### Modo No Interactivo

Para scripts automatizados:

```bash
my_verisure auth login --non-interactive
# Falla si requiere OTP
```

### Modo Batch

Para automatización completa:

```bash
my_verisure alarm arm --mode away --no-confirm
# No solicita confirmación
```

## Opciones Globales

```bash
-v, --verbose          # Habilitar logging detallado
--non-interactive      # Deshabilitar prompts interactivos
```

## Ejemplos de Uso

### Flujo Completo de Autenticación

```bash
# 1. Iniciar sesión (maneja OTP automáticamente)
my_verisure auth login

# 2. Verificar estado de autenticación
my_verisure auth status

# 3. Ver instalaciones disponibles
my_verisure info installations

# 3. Ver estado de alarma
my_verisure alarm status

# 4. Armar alarma
my_verisure alarm arm --mode away

# 5. Verificar estado
my_verisure alarm status

# 6. Desarmar alarma
my_verisure alarm disarm

# 7. Cerrar sesión
my_verisure auth logout
```

### Script de Automatización

```bash
#!/bin/bash
# script.sh

# Armar alarma al salir de casa
my_verisure alarm arm --mode away --no-confirm

# Verificar que se armó correctamente
my_verisure alarm status
```

### Verificación de Estado

```bash
# Ver todas las instalaciones
my_verisure info installations

# Ver servicios de una instalación específica
my_verisure info services --installation-id 12345678A

# Ver estado de alarma
my_verisure alarm status --installation-id 12345678A
```

## Arquitectura

El CLI está construido sobre la misma arquitectura que Home Assistant:

```
core/                    # Código común (API, repositorios, casos de uso)
├── api/                # Cliente HTTP y modelos
├── repositories/       # Interfaces e implementaciones
├── use_cases/         # Lógica de negocio
└── dependency_injection/ # Inyección de dependencias

cli/                    # Interfaz de línea de comandos
├── commands/          # Comandos individuales
├── utils/             # Utilidades compartidas
└── main.py           # Punto de entrada

custom_components/     # Integración de Home Assistant
└── my_verisure/      # Componente de HA
```

### Ventajas de esta Arquitectura

- ✅ **Reutilización total**: Mismo código para CLI y Home Assistant
- ✅ **Consistencia**: Mismo comportamiento en ambas interfaces
- ✅ **Mantenimiento**: Cambios se reflejan automáticamente
- ✅ **Testing**: Puedes probar la misma lógica desde CLI
- ✅ **Arquitectura limpia**: No duplicación de código

## Gestión de Sesión Persistente

El CLI mantiene la sesión entre comandos usando un archivo de configuración:

### Ubicación del Archivo de Sesión
```bash
~/.my_verisure/session.json
```

### Comportamiento
- **Login**: Las credenciales se guardan automáticamente
- **Verificación**: El CLI verifica si la sesión sigue siendo válida
- **Reautenticación**: Si la sesión expira, solicita credenciales nuevamente
- **Logout**: Elimina completamente el archivo de sesión

### Ejemplo de Uso
```bash
# Primera vez - requiere login completo
python my_verisure_cli.py auth login

# Comandos posteriores - usa sesión guardada
python my_verisure_cli.py auth status
python my_verisure_cli.py info installations

# Si la sesión expira, solicita reautenticación automáticamente
python my_verisure_cli.py alarm status

# Logout explícito - elimina sesión
python my_verisure_cli.py auth logout
```

## Flujo OTP

El CLI maneja automáticamente el flujo OTP cuando es necesario:

1. **Login inicial**: Intenta autenticación directa
2. **Si requiere OTP**: 
   - Muestra teléfonos disponibles
   - Usuario selecciona teléfono
   - Envía código OTP
   - Usuario introduce código
   - Verifica OTP
3. **Continúa**: Con el comando original

## Troubleshooting

### Error de Autenticación

```bash
# Verificar credenciales
my_verisure auth status

# Reintentar login
my_verisure auth logout
my_verisure auth login
```

### Error de Conexión

```bash
# Habilitar logging detallado
my_verisure --verbose auth login
```

### Error de OTP

```bash
# El CLI maneja automáticamente el flujo OTP
# Si falla, verificar que el teléfono esté disponible
my_verisure auth login
```

## Desarrollo

### Estructura de Comandos

Para añadir un nuevo comando:

1. Crear clase en `cli/commands/`
2. Heredar de `BaseCommand`
3. Implementar método `execute()`
4. Añadir al parser en `cli/main.py`

### Testing

```bash
# Probar autenticación
python my_verisure_cli.py auth login

# Probar comandos con logging detallado
python my_verisure_cli.py --verbose info installations
```

## Licencia

Misma licencia que el proyecto principal.
