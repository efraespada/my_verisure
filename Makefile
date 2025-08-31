# Makefile para My Verisure Project
# Comandos útiles para desarrollo y testing

.PHONY: help test test-cli test-core test-all lint type-check clean install dev-setup

# Variables
PYTHON = python3
VENV = venv
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

# Colores para la salida
GREEN = \033[0;32m
RED = \033[0;31m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo "$(BLUE)My Verisure - Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Instalar dependencias del proyecto
	@echo "$(BLUE)Instalando dependencias...$(NC)"
	$(PIP) install -r requirements.txt

dev-setup: ## Configurar entorno de desarrollo
	@echo "$(BLUE)Configurando entorno de desarrollo...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Creando entorno virtual...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "$(YELLOW)Activando entorno virtual...$(NC)"
	@echo "$(GREEN)Para activar el entorno virtual, ejecuta: source $(VENV)/bin/activate$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-asyncio flake8 mypy

test: ## Ejecutar todos los tests
	@echo "$(BLUE)Ejecutando todos los tests...$(NC)"
	$(PYTHON) run_all_tests.py

test-cli: ## Ejecutar solo tests del CLI
	@echo "$(BLUE)Ejecutando tests del CLI...$(NC)"
	cd cli/tests && $(PYTEST) -v

test-core: ## Ejecutar solo tests del Core
	@echo "$(BLUE)Ejecutando tests del Core...$(NC)"
	cd core/tests && $(PYTEST) -v

test-fast: ## Ejecutar tests rápidos (sin integración)
	@echo "$(BLUE)Ejecutando tests rápidos...$(NC)"
	cd cli/tests && $(PYTEST) test_input_helpers.py test_commands.py -v

test-coverage: ## Ejecutar tests con cobertura
	@echo "$(BLUE)Ejecutando tests con cobertura...$(NC)"
	cd cli/tests && $(PYTEST) --cov=cli --cov-report=term-missing --cov-report=html

lint: ## Ejecutar linting del código
	@echo "$(BLUE)Ejecutando linting...$(NC)"
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 cli/ core/ custom_components/; \
		echo "$(GREEN)Linting completado$(NC)"; \
	else \
		echo "$(YELLOW)flake8 no está instalado. Instalando...$(NC)"; \
		$(PIP) install flake8; \
		flake8 cli/ core/ custom_components/; \
	fi

type-check: ## Ejecutar verificación de tipos
	@echo "$(BLUE)Ejecutando verificación de tipos...$(NC)"
	@if command -v mypy >/dev/null 2>&1; then \
		mypy cli/ core/; \
		echo "$(GREEN)Verificación de tipos completada$(NC)"; \
	else \
		echo "$(YELLOW)mypy no está instalado. Instalando...$(NC)"; \
		$(PIP) install mypy; \
		mypy cli/ core/; \
	fi

clean: ## Limpiar archivos temporales y cache
	@echo "$(BLUE)Limpiando archivos temporales...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "$(GREEN)Limpieza completada$(NC)"

format: ## Formatear código con black
	@echo "$(BLUE)Formateando código...$(NC)"
	@if command -v black >/dev/null 2>&1; then \
		black cli/ core/ custom_components/; \
		echo "$(GREEN)Formateo completado$(NC)"; \
	else \
		echo "$(YELLOW)black no está instalado. Instalando...$(NC)"; \
		$(PIP) install black; \
		black cli/ core/ custom_components/; \
	fi

check: ## Ejecutar todas las verificaciones (lint, type-check, test)
	@echo "$(BLUE)Ejecutando todas las verificaciones...$(NC)"
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test-fast

ci: ## Comandos para CI/CD
	@echo "$(BLUE)Ejecutando pipeline de CI...$(NC)"
	@$(MAKE) clean
	@$(MAKE) install
	@$(MAKE) check
	@$(MAKE) test

# Comandos específicos para desarrollo
dev-test: ## Ejecutar tests en modo desarrollo (con más información)
	@echo "$(BLUE)Ejecutando tests en modo desarrollo...$(NC)"
	cd cli/tests && $(PYTEST) -v -s --tb=long

watch: ## Ejecutar tests en modo watch (requiere pytest-watch)
	@echo "$(BLUE)Ejecutando tests en modo watch...$(NC)"
	@if command -v ptw >/dev/null 2>&1; then \
		cd cli/tests && ptw -- -v; \
	else \
		echo "$(YELLOW)pytest-watch no está instalado. Instalando...$(NC)"; \
		$(PIP) install pytest-watch; \
		cd cli/tests && ptw -- -v; \
	fi

# Comandos para debugging
debug-test: ## Ejecutar tests con debugging
	@echo "$(BLUE)Ejecutando tests con debugging...$(NC)"
	cd cli/tests && $(PYTEST) -v -s --pdb

# Comandos para reportes
report: ## Generar reporte de tests
	@echo "$(BLUE)Generando reporte de tests...$(NC)"
	cd cli/tests && $(PYTEST) --cov=cli --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Reporte generado en htmlcov/index.html$(NC)"

# Comandos para el CLI
cli-help: ## Mostrar ayuda del CLI
	@echo "$(BLUE)Mostrando ayuda del CLI...$(NC)"
	$(PYTHON) my_verisure_cli.py --help

cli-test: ## Probar el CLI básico
	@echo "$(BLUE)Probando el CLI...$(NC)"
	$(PYTHON) my_verisure_cli.py auth --help
	$(PYTHON) my_verisure_cli.py info --help
	$(PYTHON) my_verisure_cli.py alarm --help
