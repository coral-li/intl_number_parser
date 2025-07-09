# Task 02 – Locale Candidate Definitions

## Description
Design data structures representing possible locale number formats. Start with the six common permutations of decimal and thousands separators (dot/comma/space) defined in REQUIREMENTS.md.

Create a `LocaleCandidate` `@dataclass` with at least:
- `decimal: str` – decimal separator character
- `thousands: str | None` – thousands separator (None if not used)
- `group_size: int` – expected digits per group (default 3)
- `score: int` – mutable evidence score (initial 0)

Provide `COMMON_CANDIDATES: list[LocaleCandidate]` covering:
1. `1,234.56`
2. `1.234,56`
3. `1 234,56` (NBSP thousands, comma decimal)
4. `1 234.56` (space thousands, dot decimal)
5. `1'234.56` (apostrophe thousands, dot decimal) – Swiss style
6. `1 234 567,89` (space thousands, comma decimal)

## Acceptance Criteria
- Data model lives in `intl_number_parser/locale.py` fully type-hinted.
- Factory method `all_candidates()` returns a fresh list with score 0 each call.
- Comprehensive docstrings describing each field.
- Mypy passes with no errors.

## Notes
- Thousands separator may coincide with space; be explicit in candidate list.

## References
- REQUIREMENTS.md – Locale Autodetection Strategy. 