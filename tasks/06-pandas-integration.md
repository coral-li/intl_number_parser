# Task 06 – Pandas Vectorised Integration

## Description
Provide `parse_series(series: pd.Series, detector: LocaleDetector | None = None) -> pd.Series` that vectorises number parsing without Python loops.

Implementation ideas:
- Use `series.astype(str).str` vectorised string ops plus `series.apply` only where necessary.
- Leverage `numba` or Cython optional acceleration (nice-to-have).
- Return `pd.Series` of `float64`, `Int64`, or `Decimal` objects, preserving NA values.

## Acceptance Criteria
- Lives in `intl_number_parser/pandas_adapter.py` with optional dependency on pandas.
- Works with mixed integer/decimal columns.
- Supports `.convert_dtypes()` friendly return types.
- Docstring includes usage example.
- Unit tests with series of 10 000 values run < 0.5 s.

## Notes
- Provide a fallback if pandas not installed (raise ImportError).

## References
- REQUIREMENTS.md – Usability & API Design. 