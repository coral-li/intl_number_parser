# Task 01 – Unicode Normalization & Digit Mapping Utility

## Description
Implement a pure-Python utility that converts any numeric token into a canonical ASCII representation prior to parsing.

The function must:
1. Apply Unicode Normalisation Form KC (NFKC).
2. Replace non-breaking spaces and other Unicode space separators with an ASCII space.
3. Map all known Unicode digit blocks (Arabic-Indic, Devanagari, Full-width, etc.) to ASCII `0-9`.
4. Leave ASCII digits and punctuation unchanged.

## Acceptance Criteria
- `normalize_token(token: str) -> str` returns a string containing only `[0-9 . , - + e E]` and ASCII spaces.
- Handles negative signs and leading `+` correctly.
- Round-trip examples provided in tests pass (see examples below).
- Executes in O(n) time and without external dependencies (only Python stdlib).
- 100 % branch coverage for this module.

## Example Cases
| Input | Output |
|------|--------|
| "٤٬٥٦٧٫٨٩" (Arabic-Indic) | "4567.89" |
| "1 234,56" (NBSP thousands) | "1 234,56" |
| "５．２" (Full-width) | "5.2" |

## Notes
- Use `unicodedata.normalize` and `unicodedata.digit`.
- Keep this utility in `intl_number_parser/unicode.py`.

## References
- [Unicode Standard Annex #44](https://www.unicode.org/reports/tr44/)
- REQUIREMENTS.md – Functional Capabilities, step 1. 