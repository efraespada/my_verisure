#!/usr/bin/env python3
"""
Script para ejecutar coverage sin conflictos.
Este script ejecuta todos los tests con coverage y genera reportes.
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
    UNDERLINE = '\033[4m'

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

def run_coverage():
    """Ejecutar coverage completo usando coverage directamente."""
    print_section("Running Coverage Analysis")
    
    # Limpiar datos de coverage anteriores
    print_info("Cleaning previous coverage data...")
    run_command(["python", "-m", "coverage", "erase"])
    
    # Ejecutar tests con coverage
    print_info("Running tests with coverage...")
    cmd = [
        "python", "-m", "coverage", "run", "-m", "pytest",
        "cli/tests",
        "core/tests"
    ]
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("Tests completed successfully")
        
        # Generar reportes
        print_info("Generating coverage reports...")
        
        # Reporte de terminal
        term_result = run_command(["python", "-m", "coverage", "report", "--show-missing"])
        if term_result['success']:
            print_success("Terminal report generated")
            if term_result['stdout']:
                print("\nCoverage Summary:")
                print(term_result['stdout'])
        
        # Reporte HTML
        html_result = run_command(["python", "-m", "coverage", "html", "--directory=htmlcov"])
        if html_result['success']:
            print_success("HTML report generated")
            print_info("HTML report available at: htmlcov/index.html")
        
        # Reporte XML
        xml_result = run_command(["python", "-m", "coverage", "xml", "-o", "coverage.xml"])
        if xml_result['success']:
            print_success("XML report generated")
            print_info("XML report available at: coverage.xml")
        
        return True
    else:
        print_error("Tests failed")
        if result['stdout']:
            print("STDOUT:")
            print(result['stdout'])
        if result['stderr']:
            print("STDERR:")
            print(result['stderr'])
        return False

def run_coverage_cli_only():
    """Ejecutar coverage solo para CLI."""
    print_section("Running CLI Coverage Analysis")
    
    # Limpiar datos de coverage anteriores
    print_info("Cleaning previous coverage data...")
    run_command(["python", "-m", "coverage", "erase"])
    
    # Ejecutar tests CLI con coverage
    print_info("Running CLI tests with coverage...")
    cmd = [
        "python", "-m", "coverage", "run", "-m", "pytest",
        "cli/tests"
    ]
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("CLI tests completed successfully")
        
        # Generar reportes
        print_info("Generating CLI coverage reports...")
        
        # Reporte de terminal
        term_result = run_command(["python", "-m", "coverage", "report", "--show-missing"])
        if term_result['success']:
            print_success("CLI terminal report generated")
            if term_result['stdout']:
                print("\nCLI Coverage Summary:")
                print(term_result['stdout'])
        
        # Reporte HTML
        html_result = run_command(["python", "-m", "coverage", "html", "--directory=htmlcov/cli"])
        if html_result['success']:
            print_success("CLI HTML report generated")
            print_info("HTML report available at: htmlcov/cli/index.html")
        
        return True
    else:
        print_error("CLI tests failed")
        if result['stdout']:
            print(result['stdout'])
        if result['stderr']:
            print(result['stderr'])
        return False

def run_coverage_core_only():
    """Ejecutar coverage solo para Core."""
    print_section("Running Core Coverage Analysis")
    
    # Limpiar datos de coverage anteriores
    print_info("Cleaning previous coverage data...")
    run_command(["python", "-m", "coverage", "erase"])
    
    # Ejecutar tests Core con coverage
    print_info("Running Core tests with coverage...")
    cmd = [
        "python", "-m", "coverage", "run", "-m", "pytest",
        "core/tests"
    ]
    
    result = run_command(cmd)
    
    if result['success']:
        print_success("Core tests completed successfully")
        
        # Generar reportes
        print_info("Generating Core coverage reports...")
        
        # Reporte de terminal
        term_result = run_command(["python", "-m", "coverage", "report", "--show-missing"])
        if term_result['success']:
            print_success("Core terminal report generated")
            if term_result['stdout']:
                print("\nCore Coverage Summary:")
                print(term_result['stdout'])
        
        # Reporte HTML
        html_result = run_command(["python", "-m", "coverage", "html", "--directory=htmlcov/core"])
        if html_result['success']:
            print_success("Core HTML report generated")
            print_info("HTML report available at: htmlcov/core/index.html")
        
        return True
    else:
        print_error("Core tests failed")
        if result['stdout']:
            print(result['stdout'])
        if result['stderr']:
            print(result['stderr'])
        return False

def main():
    """Función principal."""
    print_header("My Verisure - Coverage Analysis")
    
    # Verificar que estamos en el directorio correcto
    if not Path("cli").exists() or not Path("core").exists():
        print_error("This script must be run from the project root directory")
        sys.exit(1)
    
    # Verificar que coverage está instalado
    result = run_command(["python", "-m", "coverage", "--version"])
    if not result['success']:
        print_error("coverage is not installed. Please install it with: pip install coverage")
        sys.exit(1)
    
    start_time = time.time()
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        
        if target == "cli":
            success = run_coverage_cli_only()
        elif target == "core":
            success = run_coverage_core_only()
        else:
            print_error(f"Unknown target: {target}")
            print_info("Available targets: cli, core, all (default)")
            sys.exit(1)
    else:
        # Coverage completo por defecto
        success = run_coverage()
    
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
