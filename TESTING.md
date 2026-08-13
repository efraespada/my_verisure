# Testing Guide - My Verisure Project

Este documento explica cómo ejecutar todos los tests del proyecto My Verisure de diferentes maneras.

## 🚀 Comandos Rápidos

### Opción 1: Script de Shell (Recomendado)
```bash
# Ejecutar todos los tests
./run_tests.sh

# Solo tests del CLI
./run_tests.sh -c

# Tests rápidos (solo los que funcionan)
./run_tests.sh -f

# Con modo verbose
./run_tests.sh -f -v

# Solo linting y type checking
./run_tests.sh -l -t

# Generar reporte de cobertura
./run_tests.sh -r
```

### Opción 2: Makefile
```bash
# Ver todos los comandos disponibles
make help

# Ejecutar todos los tests
make test

# Solo tests del CLI
make test-cli

# Tests rápidos
make test-fast

# Con cobertura
make test-coverage

# Limpiar archivos temporales
make clean
```

### Opción 3: Script Python Global
```bash
# Ejecutar todos los tests del proyecto
python run_all_tests.py
```

## 📋 Tipos de Tests

### 1. Tests del CLI (`cli/tests/`)
- **test_input_helpers.py**: Tests para funciones de entrada del usuario
- **test_commands.py**: Tests para comandos del CLI
- **test_display.py**: Tests para funciones de visualización
- **test_session_manager.py**: Tests para gestión de sesiones
- **test_integration.py**: Tests de integración

### 2. Tests del Core (`custom_components/my_verisure/core/tests/`)
- Tests unitarios para la lógica de negocio
- Tests de repositorios
- Tests de casos de uso

### 3. Tests de Integración
- Tests que verifican la integración entre componentes
- Tests end-to-end

## 🛠️ Configuración del Entorno

### Requisitos
- Python 3.8+
- Entorno virtual activado
- Dependencias instaladas

### Instalación
```bash
# Crear y activar entorno virtual
python3.14 -m venv .ha-2026.8-venv
source .ha-2026.8-venv/bin/activate

# Instalar dependencias
pip install -r requirements-dev.txt

# Instalar herramientas de testing
pip install pytest pytest-cov pytest-asyncio flake8 mypy
```

## 📊 Cobertura de Tests

### Generar Reporte de Cobertura
```bash
# Con el script
./run_tests.sh -r

# Con make
make test-coverage

# Manualmente
cd cli/tests
python -m pytest --cov=cli --cov-report=html --cov-report=term-missing
```

### Ver Reporte
El reporte HTML se genera en `htmlcov/index.html`

## 🔧 Comandos Avanzados

### Modo Watch (Desarrollo)
```bash
# Ejecutar tests automáticamente cuando cambian archivos
./run_tests.sh -w

# Con make
make watch
```

### Debugging
```bash
# Ejecutar tests con debugger
make debug-test

# Con información detallada
./run_tests.sh -f -v
```

### Linting y Type Checking
```bash
# Solo linting
./run_tests.sh -l

# Solo type checking
./run_tests.sh -t

# Ambos
./run_tests.sh -l -t
```

## 📁 Estructura de Tests

```
my_verisure/
├── cli/
│   └── tests/
│       ├── test_input_helpers.py    # ✅ Funcionando (14 tests)
│       ├── test_commands.py         # ✅ Funcionando (29 tests)
│       ├── test_display.py          # ⚠️  Necesita revisión
│       ├── test_session_manager.py  # ⚠️  Necesita revisión
│       ├── test_integration.py      # ⚠️  Necesita revisión
│       └── run_tests.py             # Script local
├── core/
│   └── tests/
│       └── unit/                    # Tests unitarios del core
├── run_all_tests.py                 # Script global
├── run_tests.sh                     # Script de shell
├── Makefile                         # Comandos make
└── TESTING.md                       # Este archivo
```

## 🎯 Estado Actual de los Tests

### ✅ Tests Funcionando
- **test_input_helpers.py**: 14/14 tests pasando
- **test_commands.py**: 29/29 tests pasando
- **Total**: 43 tests pasando

### ⚠️ Tests que Necesitan Atención
- **test_display.py**: Tests de visualización
- **test_session_manager.py**: Tests de gestión de sesiones
- **test_integration.py**: Tests de integración
- **custom_components/my_verisure/core/tests/**: Tests del core

## 🐛 Solución de Problemas

### Tests se quedan colgados
Si los tests se quedan esperando input del usuario:
```bash
# Usar tests rápidos que están corregidos
./run_tests.sh -f
```

### Error de entorno virtual
```bash
# Recrear entorno virtual
rm -rf .ha-2026.8-venv
python3.14 -m venv .ha-2026.8-venv
source .ha-2026.8-venv/bin/activate
pip install -r requirements-dev.txt
```

### Error de dependencias
```bash
# Instalar dependencias de testing
pip install pytest pytest-cov pytest-asyncio flake8 mypy
```

## 📝 Mejores Prácticas

1. **Ejecutar tests antes de hacer commit**
   ```bash
   ./run_tests.sh -f
   ```

2. **Usar tests rápidos durante desarrollo**
   ```bash
   ./run_tests.sh -f -v
   ```

3. **Verificar linting y tipos**
   ```bash
   ./run_tests.sh -l -t
   ```

4. **Generar reporte de cobertura antes de release**
   ```bash
   ./run_tests.sh -r
   ```

## 🔄 CI/CD

Para integración continua, usar:
```bash
make ci
```

Esto ejecuta:
1. Limpieza
2. Instalación de dependencias
3. Linting y type checking
4. Tests

## 📞 Soporte

Si tienes problemas con los tests:
1. Verificar que el entorno virtual esté activado
2. Ejecutar `./run_tests.sh --help` para ver opciones
3. Usar `./run_tests.sh -f -v` para más información
4. Revisar este documento para soluciones comunes
