# Task 08 – Comprehensive Test Suite

## Description
Develop an exhaustive pytest suite achieving:
- **100 % branch coverage** for core parsing modules (`unicode`, `locale`, `validation`, `detector`, `core`).
- **≥ 95 % overall** project coverage.

Tests to include:
- Parametrised cases covering all separator permutations, edge cases, scientific notation, negative/positive, whitespace variants, invalid tokens.
- Property-based tests using `hypothesis` for random numeric strings.
- Performance regression test ensuring < 1.5× slowdown between releases.

## Acceptance Criteria
- Coverage measured via `pytest-cov`; CI fails if thresholds unmet.
- Test runtime < 60 s on GitHub Actions runner.

## Notes
- Use fixtures to share `LocaleDetector` across tests.

## References
- REQUIREMENTS.md – Robustness & Code Quality. 