#!/usr/bin/env python3
"""
Script para verificar y mostrar coverage.
"""

import sys
import subprocess
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

def check_coverage_installation():
    """Verificar si coverage está instalado."""
    print_section("Verificando instalación de Coverage")
    
    # Verificar si se puede importar coverage
    result = run_command(["python", "-c", "import coverage; print('coverage importable')"])
    if result['success']:
        print_success("Coverage es importable")
        return True
    else:
        print_error("Coverage no es importable")
        print_info("STDERR: " + result['stderr'])
        return False

def check_coverage_command():
    """Verificar si el comando coverage funciona."""
    print_section("Verificando comando Coverage")
    
    result = run_command(["python", "-m", "coverage", "--version"])
    if result['success']:
        print_success("Comando coverage funciona")
        print_info(result['stdout'])
        return True
    else:
        print_error("Comando coverage no funciona")
        print_info("STDERR: " + result['stderr'])
        return False

def test_coverage_basic():
    """Probar coverage básico."""
    print_section("Probando Coverage Básico")
    
    # Limpiar datos anteriores
    run_command(["python", "-m", "coverage", "erase"])
    
    # Ejecutar un test simple con coverage
    result = run_command([
        "python", "-m", "coverage", "run", "-m", "pytest", 
        "cli/tests/test_cli.py", "-v"
    ])
    
    if result['success']:
        print_success("Tests ejecutados con coverage")
        
        # Generar reporte
        report_result = run_command(["python", "-m", "coverage", "report"])
        if report_result['success']:
            print_success("Reporte de coverage generado")
            print("\n" + "="*50)
            print("REPORTE DE COVERAGE:")
            print("="*50)
            print(report_result['stdout'])
            print("="*50)
            return True
        else:
            print_error("Error generando reporte")
            return False
    else:
        print_error("Error ejecutando tests con coverage")
        print_info("STDERR: " + result['stderr'])
        return False

def show_coverage_usage():
    """Mostrar cómo usar coverage."""
    print_section("Cómo Usar Coverage")
    
    print_info("Comandos útiles de coverage:")
    print("""
📋 Comandos Básicos:
  python -m coverage run -m pytest cli/tests          # Ejecutar tests con coverage
  python -m coverage report                           # Ver reporte en terminal
  python -m coverage html                             # Generar reporte HTML
  python -m coverage xml                              # Generar reporte XML

📋 Scripts Disponibles:
  python run_coverage.py cli                  # Coverage CLI
  python run_coverage.py core                 # Coverage Core
  python run_coverage.py                      # Coverage completo
  python run_all_tests.py                             # Todos los tests + coverage
  python run_cli_tests.py                             # Tests CLI + coverage

📋 Reportes HTML:
  - htmlcov/index.html                                # Reporte completo
  - htmlcov/cli/index.html                            # Reporte CLI
  - htmlcov/core/index.html                           # Reporte Core
""")

def main():
    """Función principal."""
    print_header("My Verisure - Coverage Checker")
    
    # Verificar que estamos en el directorio correcto
    if not Path("cli").exists() or not Path("custom_components/my_verisure/core").exists():
        print_error("This script must be run from the project root directory")
        sys.exit(1)
    
    # Verificar instalación
    coverage_installed = check_coverage_installation()
    
    if not coverage_installed:
        print_error("Coverage no está instalado correctamente")
        print_info("Instala coverage con: python -m pip install coverage")
        sys.exit(1)
    
    # Verificar comando
    coverage_working = check_coverage_command()
    
    if coverage_working:
        print_success("Coverage está funcionando correctamente")
        
        # Probar coverage básico
        test_success = test_coverage_basic()
        
        if test_success:
            print_success("🎉 Coverage está completamente funcional!")
        else:
            print_warning("Coverage instalado pero hay problemas al ejecutarlo")
    else:
        print_error("Coverage no está funcionando correctamente")
    
    # Mostrar uso
    show_coverage_usage()
    
    print_header("Resumen")
    if coverage_installed and coverage_working:
        print_success("✅ Coverage está listo para usar")
    else:
        print_warning("⚠️  Coverage necesita configuración adicional")

if __name__ == "__main__":
    main()
