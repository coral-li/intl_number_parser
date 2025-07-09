# International Number Parser – Requirements

## Functional Capabilities
- Works with **any** known international number format; locale-autodetection accuracy ≥ 99 %.
- Requires **no prior knowledge** of the input format—the library must infer and parse automatically.
- Converts input to the canonical Python numeric string accepted by `float()` (or `int` if it's an integer number).
- Handles negative numbers, non-breaking spaces, scientific notation, and numbers embedded in free text.
- Lenient (best-effort) parsing.
- Preserves precision: integers ≤ 2⁶³−1 and decimals up to 34 significant digits.

## Locale Autodetection Strategy (evidence-accumulating)

- Optimised for *series* parsing where all values share one locale; singleton parsing remains supported but may return lower confidence.
- Begin with a compact candidate pool covering the six common separator permutations (comma/dot/space as decimal vs thousands).
- For each incoming token:
  1. Unicode-normalise (e.g., NBSP → space, Arabic-Indic digits → ASCII).
  2. Validate against every candidate:
     - single decimal separator only,
     - thousands groups must be exactly three digits each (unless locale defines otherwise),
     - scientific notation: thousands separators disallowed inside mantissa.
  3. Update candidate scores (+1 on pass, −1 on structural violation).
- Eliminate candidates whose score falls below a dynamic threshold; lock in the winner once either:
  - only one candidate remains **or**
  - its score exceeds the runner-up by ≥ 10×.
- Expose `detector.confidence` (0 – 1) and allow callers to freeze or override the locale at any time.
- Target ≥ 99 % autodetection accuracy for homogeneous series of ≥ 5 values drawn from supported locales.

## Usability & API Design
- Simple, pure-function API.
- First-class Pandas support via `parse_series()` that operates vectorially (no Python loops).

## Robustness & Code Quality
- Production-ready codebase with full type hints (PEP 484) and **mypy-clean**.
- **100 % branch coverage** for core parsing; **≥ 95 % overall** test coverage.
- Conforms to `black`, `isort`, `ruff`; **no linter warnings**.
- Security-hardened: no use of `eval`, reflection, or vulnerable regex patterns.

## Operations & Deployment
- Compatible with **Python 3.8 – 3.13** and latest PyPy 3.
- Distribute wheels for Linux, macOS, Windows; provide a pure-Python fallback.
- Licensed under **MIT** or **Apache-2.0**.
- Follow **Semantic Versioning**; maintain a CHANGELOG per *Keep A Changelog*.
- Documentation built with Sphinx: usage guide, locale matrix, benchmarks, migration notes.
