#!/usr/bin/env python3
"""Script específico para ejecutar tests del CLI de My Verisure."""

import sys
import os
import subprocess
import time
from pathlib import Path

# Colores para la salida
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title: str):
    """Imprimir un encabezado con formato."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}{Colors.ENDC}")

def print_section(title: str):
    """Imprimir una sección con formato."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}📋 {title}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-'*50}{Colors.ENDC}")

def print_success(message: str):
    """Imprimir un mensaje de éxito."""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message: str):
    """Imprimir un mensaje de error."""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Imprimir un mensaje de advertencia."""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_info(message: str):
    """Imprimir un mensaje informativo."""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def run_command(command: list, cwd: str = None) -> dict:
    """Ejecutar un comando y retornar el resultado."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos de timeout
        )
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': 'Command timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def run_cli_tests() -> bool:
    """Ejecutar tests del CLI."""
    print_section("CLI Tests")
    
    cli_tests_dir = Path("cli/tests")
    if not cli_tests_dir.exists():
        print_error(f"Directorio de tests CLI no encontrado: {cli_tests_dir}")
        return False
    
    # Ejecutar tests del CLI
    result = run_command(
        ["python", "-m", "pytest", "-v", "--tb=short"],
        cwd=str(cli_tests_dir)
    )
    
    if result['success']:
        print_success("Tests del CLI completados exitosamente")
        if result['stdout']:
            # Mostrar solo el resumen final
            lines = result['stdout'].split('\n')
            for line in lines[-10:]:  # Últimas 10 líneas
                if line.strip():
                    print(f"  {line}")
        return True
    else:
        print_error("Tests del CLI fallaron")
        if result['stdout']:
            print("STDOUT:")
            print(result['stdout'])
        if result['stderr']:
            print("STDERR:")
            print(result['stderr'])
        return False

def run_linting() -> bool:
    """Ejecutar linting del código CLI."""
    print_section("CLI Code Linting")
    
    # Verificar si flake8 está disponible
    result = run_command(["flake8", "--version"])
    if not result['success']:
        print_warning("flake8 no está instalado. Saltando linting.")
        return True
    
    # Ejecutar flake8 en el directorio CLI
    if Path("cli").exists():
        print_info("Linting cli/")
        result = run_command(["flake8", "cli"])
        
        if result['success']:
            print_success("cli/ - Sin errores de linting")
            return True
        else:
            print_error("cli/ - Errores de linting encontrados")
            if result['stdout']:
                print(result['stdout'])
            return False
    
    return True

def run_cli_coverage() -> bool:
    """Ejecutar coverage para CLI."""
    print_section("CLI Coverage Report")
    
    # Usar el script dedicado para coverage de CLI
    cmd = ["python", "run_coverage.py", "cli"]
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("CLI coverage report generated successfully")
        print_info("HTML report available at: htmlcov/cli/index.html")
        return True
    else:
        print_error("CLI coverage report generation failed")
        if result['stdout']:
            print(result['stdout'])
        if result['stderr']:
            print(result['stderr'])
        return False

def main():
    """Función principal."""
    print_header("My Verisure - CLI Test Suite")
    
    # Verificar que estamos en el directorio correcto
    if not Path("cli").exists():
        print_error("Este script debe ejecutarse desde el directorio raíz del proyecto")
        sys.exit(1)
    
    start_time = time.time()
    all_success = True
    
    # Ejecutar diferentes tipos de tests
    test_suites = [
        ("CLI Tests", run_cli_tests),
        ("CLI Code Linting", run_linting),
        ("CLI Coverage Report", run_cli_coverage),
    ]
    
    results = {}
    
    for suite_name, suite_func in test_suites:
        print_header(suite_name)
        try:
            success = suite_func()
            results[suite_name] = success
            if not success:
                all_success = False
        except Exception as e:
            print_error(f"Error ejecutando {suite_name}: {e}")
            results[suite_name] = False
            all_success = False
    
    # Resumen final
    end_time = time.time()
    duration = end_time - start_time
    
    print_header("Test Results Summary")
    
    for suite_name, success in results.items():
        if success:
            print_success(f"{suite_name}: PASSED")
        else:
            print_error(f"{suite_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Tiempo total: {duration:.2f} segundos{Colors.ENDC}")
    
    if all_success:
        print_success("🎉 ¡Todos los tests del CLI pasaron exitosamente!")
        print_info("Para ejecutar con cobertura, usa: python -m pytest cli/tests --cov=cli --cov-report=html")
        sys.exit(0)
    else:
        print_error("💥 Algunos tests del CLI fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main()
