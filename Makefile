# My Verisure development and verification commands.

.PHONY: help test test-cli test-core test-ha-2026-8 lint lint-critical type-check type-check-migrated clean install dev-setup repowise

# Home Assistant Core 2026.8.1 is the only supported validation target.
HA_PYTHON ?= /tmp/ha-2026.8.1-venv/bin/python
PYTHON = $(HA_PYTHON)
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-22s %s\n", $$1, $$2}'

install: ## Install the pinned development dependencies
	$(PIP) install -r requirements-dev.txt

dev-setup: ## Install development dependencies in the selected Python environment
	$(PIP) install -r requirements-dev.txt

test: ## Run the complete repository test suite
	$(PYTHON) run_all_tests.py

test-ha-2026-8: ## Run the complete suite against Home Assistant Core 2026.8.1
	@./scripts/test-ha-2026.8.sh

test-cli: ## Run CLI tests
	$(PYTEST) cli/tests -q

test-core: ## Run application/core unit tests
	$(PYTEST) custom_components/my_verisure/core/tests -q

lint: ## Run the full Flake8 check
	$(PYTHON) -m flake8 cli custom_components scripts

lint-critical: ## Run the CI critical Flake8 check
	$(PYTHON) -m flake8 --select=E9,F63,F7,F82 cli custom_components scripts

type-check: ## Run the repository mypy check
	$(PYTHON) -m mypy --explicit-package-bases --ignore-missing-imports cli custom_components scripts

type-check-migrated: ## Run mypy on the migrated application/core layers
	$(PYTHON) -m mypy --explicit-package-bases --ignore-missing-imports \
		custom_components/my_verisure/core/api \
		custom_components/my_verisure/core/application \
		custom_components/my_verisure/core/dependency_injection \
		custom_components/my_verisure/core/repositories \
		custom_components/my_verisure/core/use_cases

clean: ## Remove Python caches and local test reports
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +

git-check: ## Verify formatting, architecture and dependency consistency
	git diff --check
	$(PYTHON) -m compileall -q custom_components scripts setup_development.py
	$(PYTHON) scripts/architecture_guard.py
	$(PIP) check

repowise: ## Run the advisory Repowise analysis
	@./scripts/repowise.sh status --format json --no-workspace .
	@./scripts/repowise.sh health --format json --no-workspace .
	@./scripts/repowise.sh dead-code --safe-only --format json --no-workspace . || true
