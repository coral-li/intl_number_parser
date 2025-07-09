# Task 05 – Core Number Parsing Engine

## Description
Implement `parse_number(token: str, detector: LocaleDetector | None = None) -> str | int` that converts an input token to the canonical Python numeric string (or int) accepted by `float()` / `int()` while preserving precision constraints:
- Integers up to 2^63-1 return `int`.
- Decimals up to 34 significant digits return a canonical **string** (caller may pass to `decimal.Decimal`).

Features to support:
- Negative and explicit positive signs.
- Scientific notation.
- Numbers embedded in free text (extract first match per call).
- Lenient parsing: best-effort even if locale uncertain.

## Acceptance Criteria
- Located in `intl_number_parser/core.py` with full type hints.
- Uses detector when provided; otherwise falls back to per-token autodetection (lower confidence OK).
- No floating-point rounding during parsing; operate on strings.
- 100 % branch coverage for this module.
- Benchmarked to parse ≥ 1 M tokens/s for ASCII inputs on modern CPU.

## Notes
- Consider using `decimal` module only for range/precision checks, not for conversion.

## References
- REQUIREMENTS.md – Functional Capabilities. 