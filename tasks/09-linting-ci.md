# Task 09 – Linting & Continuous Integration

## Description
Set up automated code quality checks and continuous integration pipeline.

Requirements:
- Enforce `black`, `isort`, and `ruff` with zero warnings.
- GitHub Actions workflow (or alternative) running on every push/PR:
  1. `python -m pip install -e .[dev]`
  2. `ruff`, `black --check`, `isort --check`.
  3. `mypy --strict`.
  4. `pytest` with coverage report.
- Status badges in README.

## Acceptance Criteria
- CI passes on Python 3.8, 3.12, and PyPy 3 latest.
- Pre-commit hooks configured for local dev.

## References
- REQUIREMENTS.md – Robustness & Code Quality, Operations & Deployment. 