# Task 03 – Candidate Validation Logic

## Description
Implement fast structural validation of a numeric token against a given `LocaleCandidate`.

Validation rules (see REQUIREMENTS.md):
1. Exactly one decimal separator permitted (or none for integers).
2. Thousands groups must be *exactly* three digits each, except the leading group which may have 1–3 digits.
3. No thousands separators allowed inside mantissa when scientific notation (`e` / `E`) present.
4. Only characters allowed after `normalize_token` are digits, decimal separator, thousands separator, exponent markers, sign characters.

Provide function:
```python
validate(token: str, candidate: LocaleCandidate) -> bool
```
that returns `True` if token conforms, `False` otherwise.

## Acceptance Criteria
- Handles both integer, decimal, and scientific notation inputs.
- Unit tests cover at least 30 diverse cases incl. edge cases.
- No regexes with catastrophic backtracking; prefer manual scanning.
- 100 % branch coverage.

## Notes
- Consider splitting validation into pre-mantissa and exponent parts.

## References
- REQUIREMENTS.md – Locale Autodetection Strategy, step 2. 