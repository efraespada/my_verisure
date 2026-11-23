# My Verisure development and verification commands.

.PHONY: help test test-cli test-core test-ha-2026-11 coverage ci lint lint-critical type-check type-check-migrated clean install dev-setup git-check distribution-check docs-check

# Primary validation target: Home Assistant Core 2026.11.2.
HA_PYTHON ?= $(CURDIR)/.ha-2026.11-venv/bin/python
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
	$(PYTEST) -c pytest.ini -q

test-ha-2026-11: ## Run the complete primary suite against HA Core 2026.11.2
	@HA_PYTHON="$(HA_PYTHON)" ./scripts/test-ha-2026.11.sh

test-cli: ## Run CLI tests
	$(PYTEST) cli/tests -q

test-core: ## Run application/core unit tests
	$(PYTEST) custom_components/my_verisure/core/tests -q

coverage: ## Run the complete suite with contextual coverage
	rm -f coverage.xml
	PYTHONPATH="$(CURDIR)" $(PYTHON) -m pytest -c pytest.ini \
		--cov=custom_components/my_verisure \
		--cov=cli --cov=scripts \
		--cov-context=test \
		--cov-report=term-missing \
		--cov-report=xml --cov-report=json:dist/project-coverage.json -q
	$(PYTHON) scripts/check_notification_coverage.py dist/project-coverage.json
	$(PYTHON) scripts/check_project_coverage.py dist/project-coverage.json
	rm -f coverage.xml device_identifiers.json dist/project-coverage.json

lint: ## Run the full Flake8 check
	$(PYTHON) -m flake8 cli custom_components scripts

lint-critical: ## Run the CI critical Flake8 check
	$(PYTHON) -m flake8 --select=E9,F cli custom_components scripts

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

docs-check: ## Check local documentation links and specification references
	$(PYTHON) scripts/check_documentation.py

git-check: ## Verify formatting, architecture and dependency consistency
	git diff --check
	$(PYTHON) -m compileall -q custom_components scripts
	$(PYTHON) scripts/architecture_guard.py
	$(PYTHON) scripts/check_documentation.py
	$(PIP) check

distribution-check: ## Validate the installable Home Assistant artifact
	$(PYTHON) scripts/validate_distribution.py

ci: ## Run all local release-quality gates
	$(MAKE) test-ha-2026-11
	$(MAKE) type-check
	$(MAKE) lint-critical
	$(MAKE) git-check
	$(MAKE) distribution-check
	$(MAKE) coverage
