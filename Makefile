# ============================================================================
# International Number Parser - Development Makefile
# ============================================================================

.PHONY: help
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
RESET := \033[0m

# Python and dependency commands
UV := uv
UV_RUN := $(UV) run --locked --extra dev
PYTHON := $(UV_RUN) python
PYTEST := $(UV_RUN) pytest
COVERAGE := $(UV_RUN) coverage

# Project directories
SRC_DIR := intl_number_parser
TEST_DIR := tests
DOCS_DIR := docs

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "$(CYAN)International Number Parser - Development Commands$(RESET)"
	@echo ""
	@echo "$(YELLOW)Usage:$(RESET)"
	@echo "  make [target]"
	@echo ""
	@echo "$(YELLOW)Setup & Installation:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Setup/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Development:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Development/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Code Quality:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Code Quality/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Testing:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Testing/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Documentation:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Documentation/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Build & Deploy:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Build/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Maintenance:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / && /Maintenance/ {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Setup & Installation
# ============================================================================

install: ## Setup - Install package in development mode
	@echo "$(CYAN)Installing package in development mode...$(RESET)"
	$(UV) sync --locked

install-dev: ## Setup - Install package with development dependencies
	@echo "$(CYAN)Installing package with development dependencies...$(RESET)"
	$(UV) sync --locked --extra dev

install-all: install-dev setup-pre-commit ## Setup - Complete development setup

setup-pre-commit: ## Setup - Install and configure pre-commit hooks
	@echo "$(CYAN)Setting up pre-commit hooks...$(RESET)"
	$(UV_RUN) pre-commit install
	$(UV_RUN) pre-commit install --hook-type commit-msg

# ============================================================================
# Development
# ============================================================================

dev: install-dev setup-pre-commit ## Development - Quick setup for development
	@echo "$(GREEN)Development environment ready!$(RESET)"

upgrade: ## Development - Upgrade all dependencies
	@echo "$(CYAN)Upgrading dependencies...$(RESET)"
	$(UV) lock --upgrade
	$(UV) sync --locked --extra dev

# ============================================================================
# Code Quality
# ============================================================================

format: ## Code Quality - Format code with ruff
	@echo "$(CYAN)Formatting code with ruff...$(RESET)"
	$(UV_RUN) ruff format .

lint: ## Code Quality - Run linter (ruff)
	@echo "$(CYAN)Running linter...$(RESET)"
	$(UV_RUN) ruff check .

lint-fix: ## Code Quality - Run linter and fix issues
	@echo "$(CYAN)Running linter with fixes...$(RESET)"
	$(UV_RUN) ruff check . --fix

typecheck: ## Code Quality - Run type checker (mypy)
	@echo "$(CYAN)Running type checker...$(RESET)"
	$(UV_RUN) mypy $(SRC_DIR)

security: ## Code Quality - Run security scanner (bandit)
	@echo "$(CYAN)Running security scanner...$(RESET)"
	$(UV_RUN) bandit -r $(SRC_DIR)

safety: ## Code Quality - Check for known security vulnerabilities
	@echo "$(CYAN)Checking for known vulnerabilities...$(RESET)"
	$(UV_RUN) safety check

check: lint typecheck security ## Code Quality - Run all code quality checks

check-all: lint typecheck security safety ## Code Quality - Run all checks including security

pre-commit: ## Code Quality - Run pre-commit hooks manually
	@echo "$(CYAN)Running pre-commit hooks...$(RESET)"
	$(UV_RUN) pre-commit run --all-files

# ============================================================================
# Testing
# ============================================================================

test: ## Testing - Run tests
	@echo "$(CYAN)Running tests...$(RESET)"
	$(PYTEST) $(TEST_DIR)

test-verbose: ## Testing - Run tests with verbose output
	@echo "$(CYAN)Running tests (verbose)...$(RESET)"
	$(PYTEST) $(TEST_DIR) -v

test-parallel: ## Testing - Run tests in parallel
	@echo "$(CYAN)Running tests in parallel...$(RESET)"
	$(PYTEST) $(TEST_DIR) -n auto

test-coverage: ## Testing - Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

test-coverage-xml: ## Testing - Run tests with XML coverage report
	@echo "$(CYAN)Running tests with XML coverage...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=xml

test-fast: ## Testing - Run tests with minimal output
	@echo "$(CYAN)Running fast tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -q

test-watch: ## Testing - Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(RESET)"
	$(PYTEST) $(TEST_DIR) -f

coverage-report: ## Testing - Generate coverage report
	@echo "$(CYAN)Generating coverage report...$(RESET)"
	$(COVERAGE) report
	$(COVERAGE) html

coverage-open: coverage-report ## Testing - Open coverage report in browser
	@echo "$(CYAN)Opening coverage report...$(RESET)"
	open htmlcov/index.html

# ============================================================================
# Documentation
# ============================================================================

docs: ## Documentation - Build documentation
	@echo "$(CYAN)Building documentation...$(RESET)"
	@if [ ! -d "$(DOCS_DIR)" ]; then \
		echo "$(YELLOW)Creating docs directory...$(RESET)"; \
		mkdir -p $(DOCS_DIR); \
	fi
	@if [ ! -f "$(DOCS_DIR)/conf.py" ]; then \
		echo "$(YELLOW)Initializing Sphinx documentation...$(RESET)"; \
		cd $(DOCS_DIR) && $(UV_RUN) sphinx-quickstart -q -p "International Number Parser" -a "Team" -v "0.1.0" --ext-autodoc --ext-viewcode --makefile --no-batchfile .; \
	fi
	cd $(DOCS_DIR) && make html

docs-serve: docs ## Documentation - Serve documentation locally
	@echo "$(CYAN)Serving documentation...$(RESET)"
	cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000

docs-clean: ## Documentation - Clean documentation build
	@echo "$(CYAN)Cleaning documentation...$(RESET)"
	@if [ -d "$(DOCS_DIR)" ]; then \
		cd $(DOCS_DIR) && make clean; \
	fi

# ============================================================================
# Build & Deploy
# ============================================================================

build: clean ## Build - Build distribution packages
	@echo "$(CYAN)Building distribution packages...$(RESET)"
	$(UV_RUN) python -m build

build-wheel: clean ## Build - Build wheel package only
	@echo "$(CYAN)Building wheel package...$(RESET)"
	$(UV_RUN) python -m build --wheel

build-sdist: clean ## Build - Build source distribution only
	@echo "$(CYAN)Building source distribution...$(RESET)"
	$(UV_RUN) python -m build --sdist

upload-test: build ## Build - Upload to TestPyPI
	@echo "$(CYAN)Uploading to TestPyPI...$(RESET)"
	$(UV_RUN) twine upload --repository testpypi dist/*

upload: build ## Build - Upload to PyPI
	@echo "$(RED)Uploading to PyPI...$(RESET)"
	@echo "$(YELLOW)Are you sure? This will publish to production PyPI!$(RESET)"
	@read -p "Press Enter to continue or Ctrl+C to abort..."
	$(UV_RUN) twine upload dist/*

# ============================================================================
# Maintenance
# ============================================================================

clean: ## Maintenance - Clean build artifacts
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-all: clean docs-clean ## Maintenance - Clean all artifacts including docs

reset: clean-all ## Maintenance - Reset to clean state
	@echo "$(CYAN)Resetting to clean state...$(RESET)"
	$(UV) pip uninstall intl-number-parser
	rm -rf .venv/

# ============================================================================
# Performance & Profiling
# ============================================================================

profile: ## Development - Profile code with py-spy
	@echo "$(CYAN)Profiling code...$(RESET)"
	@echo "$(YELLOW)Run your code in another terminal, then press Enter$(RESET)"
	@read -p "Press Enter to start profiling..."
	$(UV_RUN) py-spy record -o profile.svg -- python -m pytest $(TEST_DIR)

memory-profile: ## Development - Profile memory usage with memray
	@echo "$(CYAN)Profiling memory usage...$(RESET)"
	$(UV_RUN) memray run -o memory-profile.bin -m pytest $(TEST_DIR)
	$(UV_RUN) memray flamegraph memory-profile.bin

# ============================================================================
# CI/CD Helpers
# ============================================================================

ci-test: ## Development - Run CI test suite
	@echo "$(CYAN)Running CI test suite...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=xml --cov-report=term-missing

ci-check: check test-coverage ## Development - Run all CI checks

# ============================================================================
# Version Management
# ============================================================================

version: ## Development - Show current version
	@echo "$(CYAN)Current version:$(RESET)"
	@$(PYTHON) -c "import toml; print(toml.load('pyproject.toml')['project']['version'])"

# ============================================================================
# Status
# ============================================================================

status: ## Development - Show project status
	@echo "$(CYAN)Project Status:$(RESET)"
	@echo "$(YELLOW)Python version:$(RESET) $(shell $(PYTHON) --version)"
	@echo "$(YELLOW)Virtual environment:$(RESET) $(shell echo $$VIRTUAL_ENV)"
	@echo "$(YELLOW)Git branch:$(RESET) $(shell git branch --show-current 2>/dev/null || echo 'Not in git repo')"
	@echo "$(YELLOW)Git status:$(RESET) $(shell git status --porcelain 2>/dev/null | wc -l | tr -d ' ') files changed"
	@echo "$(YELLOW)Package installed:$(RESET) $(shell $(UV) pip show intl-number-parser >/dev/null 2>&1 && echo 'Yes' || echo 'No')"
	@echo "$(YELLOW)Pre-commit installed:$(RESET) $(shell $(UV_RUN) pre-commit --version >/dev/null 2>&1 && echo 'Yes' || echo 'No')"
