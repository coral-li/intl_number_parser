"""Evidence-accumulating locale detector for international number formats.

This module provides the LocaleDetector class that implements stateful
evidence-based locale detection for automatic number format recognition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .candidates import all_candidates
from .unicode import normalize_token
from .validation import validate

if TYPE_CHECKING:
    from .candidates import LocaleCandidate

# Constants for auto-lock logic
AUTO_LOCK_MULTIPLIER = 10
MIN_CANDIDATES_FOR_RATIO_LOCK = 2

# Constants for confidence calculation
RATIO_VERY_HIGH = 5
RATIO_HIGH = 3
RATIO_MEDIUM = 2


class LocaleDetector:
    """Stateful evidence-accumulating detector for locale identification.

    The LocaleDetector evaluates incoming numeric tokens, updates candidate scores
    based on validation results, and automatically locks in a winner when sufficient
    evidence is accumulated.

    Key features:
    - Evidence accumulation: +1 for validation success, -1 for structural violations
    - Auto-lock when only one candidate remains or leader has ≥10x advantage
    - Confidence scoring from 0.0 to 1.0
    - Manual freeze/override capabilities for caller control
    - Thread-safe operation (no shared mutable globals)

    Attributes:
        candidates: List of LocaleCandidate instances with mutable scores
        is_locked: True when detection is locked (auto or manual)
        confidence: Confidence score from 0.0 to 1.0
        best_candidate: Highest scoring candidate (or None if all negative)

    Examples:
        >>> detector = LocaleDetector()
        >>> detector.ingest("1,234.56")
        >>> detector.ingest("789.01")
        >>> detector.best_candidate.decimal
        '.'
        >>> detector.confidence > 0.8
        True
    """

    def __init__(self, candidates: list[LocaleCandidate] | None = None) -> None:
        """Initialize detector with candidates.

        Args:
            candidates: Optional list of LocaleCandidate instances.
                       If None, uses all common candidates with fresh scores.
        """
        self.candidates = candidates if candidates is not None else all_candidates()
        self._frozen_candidate: LocaleCandidate | None = None

    def ingest(self, token: str) -> None:
        """Process a numeric token and update candidate scores.

        Normalizes the token, validates it against each candidate, and updates
        scores based on validation results (+1 for success, -1 for failure).
        No-op if detector is frozen.

        Args:
            token: The numeric token to process
        """
        if self._frozen_candidate is not None:
            return  # Frozen - ignore ingestion

        if not token:
            return  # Empty token - no scoring

        # Normalize token using unicode normalization
        normalized_token = normalize_token(token)

        # If normalization results in empty token, don't score
        if not normalized_token:
            return

        # Update scores based on validation results
        for candidate in self.candidates:
            if validate(normalized_token, candidate):
                candidate.score += 1
            else:
                candidate.score -= 1

    @property
    def is_locked(self) -> bool:
        """True if detector is locked (manually frozen or auto-locked)."""
        if self._frozen_candidate is not None:
            return True

        # Auto-lock conditions:
        # 1. Only one candidate with non-negative score
        positive_candidates = [c for c in self.candidates if c.score >= 0]
        if len(positive_candidates) == 1:
            return True

        # 2. Leader has ≥10x advantage over runner-up
        if len(positive_candidates) >= MIN_CANDIDATES_FOR_RATIO_LOCK:
            sorted_candidates = sorted(
                positive_candidates, key=lambda c: c.score, reverse=True
            )
            leader_score = sorted_candidates[0].score
            runner_up_score = sorted_candidates[1].score

            if (
                leader_score >= AUTO_LOCK_MULTIPLIER * runner_up_score
                and runner_up_score > 0
            ):
                return True

        return False

    @property
    def confidence(self) -> float:
        """Confidence score from 0.0 to 1.0."""
        if self._frozen_candidate is not None:
            return 1.0

        best = self.best_candidate
        if best is None:
            return 0.0

        # Get scores of all candidates
        scores = [c.score for c in self.candidates]
        scores.sort(reverse=True)

        best_score = scores[0]

        # If all scores are 0, confidence is 0
        if best_score == 0:
            return 0.0

        # If only one candidate or best score is much higher, high confidence
        if len(scores) == 1 or best_score <= 0:
            return 0.5

        second_best_score = scores[1] if len(scores) > 1 else 0

        # Calculate confidence based on score separation
        if second_best_score <= 0:
            # Best is positive, others are non-positive
            # Scale confidence with the score strength - more generous scaling
            return min(0.99, 0.7 + 0.07 * best_score)

        # Both best and second-best are positive - calculate based on ratio
        ratio = best_score / max(second_best_score, 1)

        # Check for auto-lock threshold first
        if best_score >= AUTO_LOCK_MULTIPLIER * second_best_score:
            confidence = 0.98  # Auto-lock threshold
        elif ratio >= RATIO_VERY_HIGH:
            confidence = 0.97
        elif ratio >= RATIO_HIGH:
            confidence = 0.95
        elif ratio >= RATIO_MEDIUM:
            confidence = 0.85
        else:
            # Close competition
            confidence = 0.5 + (ratio - 1) * 0.1
            confidence = min(0.8, confidence)

        return confidence

    @property
    def best_candidate(self) -> LocaleCandidate | None:
        """Return the highest scoring candidate, or None if all scores negative."""
        if self._frozen_candidate is not None:
            return self._frozen_candidate

        # Find candidate with highest score
        best_candidate = None
        best_score = float("-inf")

        for candidate in self.candidates:
            if candidate.score > best_score:
                best_score = candidate.score
                best_candidate = candidate

        # Return None if best score is negative
        return best_candidate if best_score >= 0 else None

    def freeze(self, candidate: LocaleCandidate) -> None:
        """Manually freeze detector to specified candidate.

        After freezing, ingest() calls are ignored and the detector always
        returns the frozen candidate as best_candidate with confidence=1.0.

        Args:
            candidate: The LocaleCandidate to freeze to
        """
        self._frozen_candidate = candidate

    def override(self, candidate: LocaleCandidate) -> None:
        """Manually override detector to specified candidate.

        Unlike freeze(), override allows continued ingestion after setting
        the candidate. This adjusts scores to make the specified candidate
        the clear winner and trigger auto-lock.

        Args:
            candidate: The LocaleCandidate to make the winner
        """
        # Reset all scores and give the target candidate a score that triggers auto-lock
        for c in self.candidates:
            c.score = 0

        # Set target candidate score high enough to trigger 10x auto-lock rule
        # Give others a score of 1 and target 11 to ensure 11 >= 10 * 1
        for c in self.candidates:
            if c != candidate:
                c.score = 1
        candidate.score = 11

        # Don't set frozen state - allow continued ingestion
        self._frozen_candidate = None
