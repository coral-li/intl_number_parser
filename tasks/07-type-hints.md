# Task 07 – Type Hints & Static Analysis

## Description
Ensure the entire library is fully typed per PEP 484 and passes `mypy --strict` with zero errors.

## Acceptance Criteria
- All public functions, methods, and module-level constants have explicit type annotations.
- `pyproject.toml` (or `setup.cfg`) contains `mypy` configuration enabling strict checks.
- CI job fails the build if mypy finds issues.

## Notes
- Prefer `from __future__ import annotations` for forward references.
- Use `typing_extensions` for backports on Python 3.8.

## References
- REQUIREMENTS.md – Robustness & Code Quality. 