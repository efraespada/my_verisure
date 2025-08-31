#!/usr/bin/env python3
"""
Script simple para ejecutar coverage sin conflictos.
"""

import sys
import time
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

def run_coverage_cli():
    """Ejecutar coverage para CLI."""
    print_section("Running CLI Coverage Analysis")
    
    # Ejecutar tests CLI con coverage usando pytest-cov
    cmd = [
        "python", "-m", "pytest",
        "--cov=cli",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/cli",
        "--cov-fail-under=70",
        "cli/tests"
    ]
    
    print_info("Executing: " + " ".join(cmd))
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("CLI coverage analysis completed successfully")
        print_info("HTML report available at: htmlcov/cli/index.html")
        return True
    else:
        print_error("CLI coverage analysis failed")
        if result['stdout']:
            print("STDOUT:")
            print(result['stdout'])
        if result['stderr']:
            print("STDERR:")
            print(result['stderr'])
        return False

def run_coverage_core():
    """Ejecutar coverage para Core."""
    print_section("Running Core Coverage Analysis")
    
    # Ejecutar tests Core con coverage usando pytest-cov
    cmd = [
        "python", "-m", "pytest",
        "--cov=core",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/core",
        "--cov-fail-under=70",
        "core/tests"
    ]
    
    print_info("Executing: " + " ".join(cmd))
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("Core coverage analysis completed successfully")
        print_info("HTML report available at: htmlcov/core/index.html")
        return True
    else:
        print_error("Core coverage analysis failed")
        if result['stdout']:
            print("STDOUT:")
            print(result['stdout'])
        if result['stderr']:
            print("STDERR:")
            print(result['stderr'])
        return False

def run_coverage_all():
    """Ejecutar coverage para todos los módulos."""
    print_section("Running Complete Coverage Analysis")
    
    # Ejecutar tests con coverage usando pytest-cov
    cmd = [
        "python", "-m", "pytest",
        "--cov=cli",
        "--cov=core",
        "--cov=custom_components",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=70",
        "cli/tests",
        "core/tests"
    ]
    
    print_info("Executing: " + " ".join(cmd))
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("Complete coverage analysis completed successfully")
        print_info("HTML report available at: htmlcov/index.html")
        return True
    else:
        print_error("Complete coverage analysis failed")
        if result['stdout']:
            print("STDOUT:")
            print(result['stdout'])
        if result['stderr']:
            print("STDERR:")
            print(result['stderr'])
        return False

def main():
    """Función principal."""
    print_header("My Verisure - Simple Coverage Analysis")
    
    # Verificar que estamos en el directorio correcto
    if not Path("cli").exists() or not Path("core").exists():
        print_error("This script must be run from the project root directory")
        sys.exit(1)
    
    start_time = time.time()
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        
        if target == "cli":
            success = run_coverage_cli()
        elif target == "core":
            success = run_coverage_core()
        else:
            print_error(f"Unknown target: {target}")
            print_info("Available targets: cli, core, all (default)")
            sys.exit(1)
    else:
        # Coverage completo por defecto
        success = run_coverage_all()
    
    # Resumen final
    end_time = time.time()
    duration = end_time - start_time
    
    print_header("Coverage Results Summary")
    
    if success:
        print_success("🎉 Coverage analysis completed successfully!")
    else:
        print_error("💥 Coverage analysis failed")
    
    print(f"\n{Colors.BOLD}Total time: {duration:.2f} seconds{Colors.ENDC}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
