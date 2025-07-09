# Task 04 – Evidence-Accumulating Locale Detector

## Description
Build a stateful `LocaleDetector` that evaluates incoming tokens, updates candidate scores, and decides when a single locale can be considered *locked-in*.

Key behaviours:
- Initialise with `LocaleCandidate` list; expose `.candidates` with mutable scores.
- Method `ingest(token: str)`:
  1. Normalise token.
  2. For each candidate, run `validate`; `+1` on pass, `-1` on structural violation.
  3. Drop candidates falling below dynamic threshold (e.g. minScore).
- Lock-in logic: stop elimintation when
  - only one candidate remains, **or**
  - top candidate's score ≥ 10 × next best.
- Property `.confidence` returning float 0–1.
- Allow caller to `freeze(locale)` or `override(locale)` manually at any time.

## Acceptance Criteria
- `LocaleDetector` resides in `intl_number_parser/detector.py`.
- Thread-safe (no shared mutable globals).
- Public API: `ingest`, `best_candidate`, `is_locked`, `confidence`, `freeze`, `override`.
- Passes comprehensive unit tests simulating homogeneous and heterogeneous series.
- Autodetection accuracy ≥ 99 % on provided sample corpus (to be created under tests).

## Notes
- Keep computational complexity O(k) where k = #candidates per token.

## References
- REQUIREMENTS.md – Locale Autodetection Strategy. 