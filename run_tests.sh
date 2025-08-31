#!/bin/bash

# Script para ejecutar tests del proyecto My Verisure
# Uso: ./run_tests.sh [opciones]

set -e  # Salir si hay algún error

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}My Verisure - Script de Tests${NC}"
    echo ""
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help          Mostrar esta ayuda"
    echo "  -a, --all           Ejecutar todos los tests (default)"
    echo "  -c, --cli           Ejecutar solo tests del CLI"
    echo "  -o, --core          Ejecutar solo tests del Core"
    echo "  -f, --fast          Ejecutar tests rápidos"
    echo "  -l, --lint          Ejecutar linting"
    echo "  -t, --type          Ejecutar verificación de tipos"
    echo "  -v, --verbose       Modo verbose"
    echo "  -w, --watch         Modo watch (requiere pytest-watch)"
    echo "  -r, --report        Generar reporte de cobertura"
    echo ""
    echo "Ejemplos:"
    echo "  $0                  # Ejecutar todos los tests"
    echo "  $0 -c              # Solo tests del CLI"
    echo "  $0 -f -v           # Tests rápidos con verbose"
    echo "  $0 -l -t           # Solo linting y type checking"
}

# Variables por defecto
TEST_TYPE="all"
VERBOSE=false
WATCH_MODE=false
GENERATE_REPORT=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            TEST_TYPE="all"
            shift
            ;;
        -c|--cli)
            TEST_TYPE="cli"
            shift
            ;;
        -o|--core)
            TEST_TYPE="core"
            shift
            ;;
        -f|--fast)
            TEST_TYPE="fast"
            shift
            ;;
        -l|--lint)
            TEST_TYPE="lint"
            shift
            ;;
        -t|--type)
            TEST_TYPE="type"
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -w|--watch)
            WATCH_MODE=true
            shift
            ;;
        -r|--report)
            GENERATE_REPORT=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Opción desconocida $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Función para imprimir mensajes
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [[ ! -d "cli" ]] || [[ ! -d "core" ]]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar si existe el entorno virtual
if [[ ! -d "venv" ]]; then
    print_warning "No se encontró el entorno virtual. Creando uno nuevo..."
    python3 -m venv venv
    print_success "Entorno virtual creado"
fi

# Activar entorno virtual
print_info "Activando entorno virtual..."
source venv/bin/activate

# Verificar que las dependencias estén instaladas
if ! python -c "import pytest" 2>/dev/null; then
    print_warning "pytest no está instalado. Instalando dependencias..."
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-asyncio
fi

# Función para ejecutar tests del CLI
run_cli_tests() {
    print_info "Ejecutando tests del CLI..."
    cd cli/tests
    
    if [[ "$VERBOSE" == true ]]; then
        python -m pytest -v -s
    else
        python -m pytest -v
    fi
    
    cd ../..
}

# Función para ejecutar tests del Core
run_core_tests() {
    print_info "Ejecutando tests del Core..."
    if [[ ! -d "core/tests" ]]; then
        print_warning "No se encontraron tests del Core"
        return 0
    fi
    
    cd core/tests
    
    if [[ "$VERBOSE" == true ]]; then
        python -m pytest -v -s
    else
        python -m pytest -v
    fi
    
    cd ../..
}

# Función para ejecutar tests rápidos
run_fast_tests() {
    print_info "Ejecutando tests rápidos..."
    cd cli/tests
    
    if [[ "$VERBOSE" == true ]]; then
        python -m pytest test_input_helpers.py test_commands.py -v -s
    else
        python -m pytest test_input_helpers.py test_commands.py -v
    fi
    
    cd ../..
}

# Función para ejecutar linting
run_linting() {
    print_info "Ejecutando linting..."
    
    if ! command -v flake8 &> /dev/null; then
        print_warning "flake8 no está instalado. Instalando..."
        pip install flake8
    fi
    
    if flake8 cli/ core/ custom_components/; then
        print_success "Linting completado sin errores"
    else
        print_error "Se encontraron errores de linting"
        return 1
    fi
}

# Función para ejecutar type checking
run_type_checking() {
    print_info "Ejecutando verificación de tipos..."
    
    if ! command -v mypy &> /dev/null; then
        print_warning "mypy no está instalado. Instalando..."
        pip install mypy
    fi
    
    if mypy cli/ core/; then
        print_success "Verificación de tipos completada sin errores"
    else
        print_error "Se encontraron errores de tipos"
        return 1
    fi
}

# Función para generar reporte
generate_report() {
    print_info "Generando reporte de cobertura..."
    cd cli/tests
    
    python -m pytest --cov=cli --cov-report=html --cov-report=term-missing
    
    cd ../..
    print_success "Reporte generado en htmlcov/index.html"
}

# Función para modo watch
run_watch_mode() {
    print_info "Ejecutando tests en modo watch..."
    
    if ! command -v ptw &> /dev/null; then
        print_warning "pytest-watch no está instalado. Instalando..."
        pip install pytest-watch
    fi
    
    cd cli/tests
    ptw -- -v
}

# Ejecutar según el tipo de test seleccionado
case $TEST_TYPE in
    "all")
        print_info "Ejecutando todos los tests..."
        if [[ "$WATCH_MODE" == true ]]; then
            run_watch_mode
        else
            python run_all_tests.py
        fi
        ;;
    "cli")
        run_cli_tests
        ;;
    "core")
        run_core_tests
        ;;
    "fast")
        run_fast_tests
        ;;
    "lint")
        run_linting
        ;;
    "type")
        run_type_checking
        ;;
    *)
        print_error "Tipo de test desconocido: $TEST_TYPE"
        exit 1
        ;;
esac

# Generar reporte si se solicitó
if [[ "$GENERATE_REPORT" == true ]]; then
    generate_report
fi

print_success "Tests completados"
