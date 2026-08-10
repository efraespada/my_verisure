#!/usr/bin/env python3
"""Script global para ejecutar todos los tests del proyecto My Verisure."""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import List, Dict

PYTHON = sys.executable
CORE_TESTS = "custom_components/my_verisure/core/tests"

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

def run_command(command: List[str], cwd: str = None, capture_output: bool = True) -> Dict:
    """Ejecutar un comando y retornar el resultado."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
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

def run_pytest_tests(test_path: str, test_name: str = None) -> bool:
    """Ejecutar tests con pytest."""
    print_section(f"Running {test_name or test_path} tests")
    
    if not Path(test_path).exists():
        print_warning(f"Test path not found: {test_path}")
        return True  # No es un error si no hay tests
    
    # Comando base de pytest
    cmd = [PYTHON, "-m", "pytest", test_path, "-v"]
    
    # Ejecutar tests
    result = run_command(cmd)
    
    if result['success']:
        print_success(f"{test_name or test_path} tests completed successfully")
        if result['stdout']:
            # Mostrar solo el resumen final
            lines = result['stdout'].split('\n')
            for line in lines[-10:]:  # Últimas 10 líneas
                if line.strip():
                    print(f"  {line}")
        return True
    else:
        print_error(f"{test_name or test_path} tests failed")
        if result['stdout']:
            print("STDOUT:")
            print(result['stdout'])
        if result['stderr']:
            print("STDERR:")
            print(result['stderr'])
        return False

def run_linting() -> bool:
    """Ejecutar linting del código."""
    print_section("Code Linting")
    
    # Verificar si flake8 está disponible
    result = run_command([PYTHON, "-m", "flake8", "--version"])
    if not result['success']:
        print_warning("flake8 not installed. Skipping linting.")
        return True
    
    # Ejecutar flake8 en los directorios principales
    directories = ["cli", "custom_components"]
    all_success = True
    
    for directory in directories:
        if Path(directory).exists():
            print_info(f"Linting {directory}/")
            result = run_command([PYTHON, "-m", "flake8", directory])
            
            if result['success']:
                print_success(f"{directory}/ - No linting errors")
            else:
                print_error(f"{directory}/ - Linting errors found")
                if result['stdout']:
                    print(result['stdout'])
                all_success = False
    
    return all_success

def run_type_checking() -> bool:
    """Ejecutar verificación de tipos."""
    print_section("Type Checking")
    
    # Verificar si mypy está disponible
    result = run_command([PYTHON, "-m", "mypy", "--version"])
    if not result['success']:
        print_warning("mypy not installed. Skipping type checking.")
        return True
    
    # Ejecutar mypy en los directorios principales
    directories = ["cli", "custom_components"]
    all_success = True
    
    for directory in directories:
        if Path(directory).exists():
            print_info(f"Type checking {directory}/")
            result = run_command([PYTHON, "-m", "mypy", directory])
            
            if result['success']:
                print_success(f"{directory}/ - No type errors")
            else:
                print_error(f"{directory}/ - Type errors found")
                if result['stdout']:
                    print(result['stdout'])
                all_success = False
    
    return all_success

def run_coverage_report() -> bool:
    """Generar reporte de cobertura usando el script dedicado."""
    print_section("Coverage Report")
    
    # Usar el script dedicado para coverage
    cmd = [PYTHON, "run_coverage.py"]
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("Coverage report generated successfully")
        print_info("HTML report available at: htmlcov/index.html")
        return True
    else:
        print_error("Coverage report generation failed")
        if result['stdout']:
            print(result['stdout'])
        if result['stderr']:
            print(result['stderr'])
        return False

def main():
    """Función principal."""
    print_header("My Verisure - Test Suite")
    
    # Verificar que estamos en el directorio correcto
    if not Path("cli").exists() or not Path(CORE_TESTS).exists():
        print_error("This script must be run from the project root directory")
        sys.exit(1)
    
    # Verificar que pytest.ini existe
    if not Path("pytest.ini").exists():
        print_error("pytest.ini not found. Please ensure it exists in the project root.")
        sys.exit(1)
    
    start_time = time.time()
    all_success = True
    
    # Ejecutar diferentes tipos de tests
    test_suites = [
        ("CLI Tests", "cli/tests"),
        ("Core Tests", CORE_TESTS),
        ("Integration Tests", "."),  # Tests en el directorio raíz
    ]
    
    results = {}
    
    # Ejecutar tests
    for suite_name, test_path in test_suites:
        success = run_pytest_tests(test_path, suite_name)
        results[suite_name] = success
        if not success:
            all_success = False
    
    # Ejecutar linting y type checking
    linting_success = run_linting()
    results["Code Linting"] = linting_success
    if not linting_success:
        all_success = False
    
    type_checking_success = run_type_checking()
    results["Type Checking"] = type_checking_success
    if not type_checking_success:
        all_success = False
    
    # Generar reporte de cobertura
    coverage_success = run_coverage_report()
    results["Coverage Report"] = coverage_success
    if not coverage_success:
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
    
    print(f"\n{Colors.BOLD}Total time: {duration:.2f} seconds{Colors.ENDC}")
    
    if all_success:
        print_success("🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print_error("💥 Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
