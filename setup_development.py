#!/usr/bin/env python3
"""
Script para configurar el entorno de desarrollo.
Instala todas las dependencias necesarias automáticamente.
"""

import subprocess
import sys
from pathlib import Path

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprimir header con formato."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_section(text):
    """Imprimir sección con formato."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * len(text)}{Colors.ENDC}")

def print_success(text):
    """Imprimir mensaje de éxito."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Imprimir mensaje de error."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    """Imprimir mensaje informativo."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    """Imprimir mensaje de advertencia."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def run_command(cmd):
    """Ejecutar comando y retornar resultado."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def check_venv():
    """Verificar que estamos en un entorno virtual."""
    print_section("Verificando Entorno Virtual")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Entorno virtual activado")
        print_info(f"Python: {sys.executable}")
        return True
    else:
        print_error("No estás en un entorno virtual")
        print_info("Activa el entorno virtual con: source venv/bin/activate")
        return False

def install_requirements():
    """Instalar dependencias desde requirements.txt."""
    print_section("Instalando Dependencias")
    
    print_info("Instalando desde requirements.txt...")
    result = run_command(["python", "-m", "pip", "install", "-r", "requirements.txt"])
    
    if result['success']:
        print_success("Dependencias instaladas correctamente")
        return True
    else:
        print_error("Error instalando dependencias")
        print_info("STDERR: " + result['stderr'])
        return False

def verify_tools():
    """Verificar que las herramientas están disponibles."""
    print_section("Verificando Herramientas")
    
    tools = [
        ("pytest", "python -m pytest --version"),
        ("coverage", "python -m coverage --version"),
        ("flake8", "flake8 --version"),
        ("mypy", "mypy --version"),
        ("black", "black --version"),
    ]
    
    all_ok = True
    
    for tool_name, cmd in tools:
        result = run_command(cmd.split())
        if result['success']:
            print_success(f"{tool_name} disponible")
            print_info(result['stdout'].strip())
        else:
            print_error(f"{tool_name} no disponible")
            all_ok = False
    
    return all_ok

def run_quick_test():
    """Ejecutar un test rápido para verificar que todo funciona."""
    print_section("Test Rápido")
    
    print_info("Ejecutando test simple...")
    result = run_command(["python", "-m", "pytest", "cli/tests/test_cli.py", "-v", "--tb=short"])
    
    if result['success']:
        print_success("Test rápido exitoso")
        return True
    else:
        print_error("Test rápido falló")
        print_info("STDERR: " + result['stderr'])
        return False

def show_next_steps():
    """Mostrar próximos pasos."""
    print_section("Próximos Pasos")
    
    print_info("Ahora puedes usar estos comandos:")
    print("""
📋 Comandos Disponibles:
  python run_all_tests.py                    # Ejecutar todos los tests
  python run_cli_tests.py                    # Tests CLI
  python run_coverage.py cli         # Coverage CLI
  python run_coverage.py core        # Coverage Core
  python check_coverage.py                   # Verificar coverage

📋 Herramientas de Desarrollo:
  flake8 cli/ core/                          # Linting
  mypy cli/ core/                            # Type checking
  black cli/ core/                           # Formatear código
  python -m pytest cli/tests/ -v             # Tests CLI
  python -m pytest core/tests/ -v            # Tests Core

📋 Coverage:
  python -m coverage run -m pytest cli/tests # Coverage CLI
  python -m coverage report                  # Ver reporte
  python -m coverage html                    # Reporte HTML
""")

def main():
    """Función principal."""
    print_header("My Verisure - Setup de Desarrollo")
    
    # Verificar que estamos en el directorio correcto
    if not Path("cli").exists() or not Path("core").exists():
        print_error("This script must be run from the project root directory")
        sys.exit(1)
    
    # Verificar entorno virtual
    if not check_venv():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_requirements():
        sys.exit(1)
    
    # Verificar herramientas
    if not verify_tools():
        print_warning("Algunas herramientas no están disponibles")
        print_info("Puedes continuar, pero algunas funcionalidades no estarán disponibles")
    
    # Test rápido
    if not run_quick_test():
        print_warning("Test rápido falló")
        print_info("Puedes continuar, pero verifica que los tests funcionen")
    
    # Mostrar próximos pasos
    show_next_steps()
    
    print_header("Resumen")
    print_success("🎉 Configuración completada")
    print_info("Tu entorno de desarrollo está listo para usar")

if __name__ == "__main__":
    main()
