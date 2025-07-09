# International Number Parser

A Python library for parsing international number formats with automatic locale detection.

## 🚀 Quick Start

### Setup Development Environment

```bash
# Complete development setup (recommended)
make install-all

# Or step by step:
make install-dev          # Install with dev dependencies
make setup-pre-commit     # Setup pre-commit hooks
```

### Development Commands

```bash
# Show all available commands
make help

# Code quality
make lint                 # Run linter
make format              # Format code
make typecheck           # Type checking
make check               # Run all quality checks

# Testing
make test                # Run tests
make test-coverage       # Run tests with coverage
make coverage-open       # Open coverage report

# Development workflow
make dev                 # Quick development setup
make status              # Show project status
```

## 📋 Available Make Commands

### Setup & Installation
- `make install` - Install package in development mode
- `make install-dev` - Install package with development dependencies
- `make install-all` - Complete development setup
- `make setup-pre-commit` - Install and configure pre-commit hooks

### Code Quality
- `make format` - Format code with ruff
- `make lint` - Run linter (ruff)
- `make lint-fix` - Run linter and fix issues
- `make typecheck` - Run type checker (mypy)
- `make security` - Run security scanner (bandit)
- `make check` - Run all code quality checks
- `make pre-commit` - Run pre-commit hooks manually

### Testing
- `make test` - Run tests
- `make test-coverage` - Run tests with coverage report
- `make test-parallel` - Run tests in parallel
- `make coverage-open` - Open coverage report in browser

### Documentation
- `make docs` - Build documentation
- `make docs-serve` - Serve documentation locally

### Build & Deploy
- `make build` - Build distribution packages
- `make upload-test` - Upload to TestPyPI
- `make upload` - Upload to PyPI

### Maintenance
- `make clean` - Clean build artifacts
- `make status` - Show project status

## 🛠️ Development Workflow

1. **Initial Setup**
   ```bash
   make install-all
   ```

2. **Before Making Changes**
   ```bash
   make check        # Run all quality checks
   make test         # Run tests
   ```

3. **After Making Changes**
   ```bash
   make format       # Format code
   make lint-fix     # Fix linting issues
   make test-coverage # Run tests with coverage
   ```

4. **Pre-commit** (runs automatically on commit)
   - Code formatting (ruff)
   - Linting (ruff)
   - Type checking (mypy)
   - Security scanning (bandit)

## 🔧 Configuration

### Ruff (Linting & Formatting)
Configuration in `pyproject.toml`:
- Line length: 88 characters
- Target Python: 3.8+
- Comprehensive rule set (30+ categories)
- Per-file ignores for tests and `__init__.py`

### MyPy (Type Checking)
- Strict mode enabled
- Python 3.8+ compatibility
- Comprehensive type checking

### Pytest (Testing)
- 100% branch coverage requirement
- Parallel test execution support
- HTML and XML coverage reports

## 📦 Dependencies

### Runtime Dependencies
- `pandas>=1.5.0`
- `numpy>=1.21.0`
- `unicodedata2>=15.0.0`

### Development Dependencies
- `ruff>=0.12.0` - Linting and formatting
- `mypy>=1.10.0` - Type checking
- `pytest>=7.0.0` - Testing framework
- `pre-commit>=3.0.0` - Pre-commit hooks
- `bandit>=1.7.0` - Security scanning
- `sphinx>=5.0.0` - Documentation
- And more...

## 🎯 Project Requirements

- **Python 3.8-3.13** compatibility
- **100% branch coverage** for core parsing
- **≥95% overall** test coverage
- **mypy-clean** with strict type checking
- **No linter warnings** (ruff compliant)
- **Security hardened** (bandit validated)

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the full test suite: `make ci-check`
5. Submit a pull request

For detailed development guidelines, see `REQUIREMENTS.md`. 