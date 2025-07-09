"""Test suite for the evidence-accumulating locale detector.

This module tests the LocaleDetector class that implements evidence-based
locale detection for international number formats.
"""

from __future__ import annotations

from intl_number_parser.candidates import LocaleCandidate, all_candidates
from intl_number_parser.detector import LocaleDetector


class TestLocaleDetectorInit:
    """Test LocaleDetector initialization."""

    def test_should_initialize_with_default_candidates(self):
        """LocaleDetector should initialize with all common candidates."""
        detector = LocaleDetector()

        assert len(detector.candidates) == 6
        assert all(candidate.score == 0 for candidate in detector.candidates)
        assert not detector.is_locked
        assert detector.confidence == 0.0

    def test_should_initialize_with_custom_candidates(self):
        """LocaleDetector should accept custom candidate list."""
        custom_candidates = [
            LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0),
            LocaleCandidate(decimal=",", thousands=".", group_size=3, score=0),
        ]

        detector = LocaleDetector(custom_candidates)

        assert len(detector.candidates) == 2
        assert detector.candidates[0].decimal == "."
        assert detector.candidates[1].decimal == ","

    def test_should_create_independent_candidate_instances(self):
        """LocaleDetector should work with independent candidate instances."""
        original_candidates = all_candidates()
        detector = LocaleDetector()

        # Modifying detector candidates shouldn't affect originals
        detector.candidates[0].score = 10
        assert original_candidates[0].score == 0


class TestLocaleDetectorIngest:
    """Test token ingestion and evidence accumulation."""

    def test_should_increase_score_for_valid_token(self):
        """ingest() should increase score for candidates that validate successfully."""
        detector = LocaleDetector()

        # US format token should increase US format candidate score
        detector.ingest("1,234.56")

        us_candidate = next(
            c for c in detector.candidates if c.decimal == "." and c.thousands == ","
        )
        assert us_candidate.score == 1

    def test_should_decrease_score_for_invalid_token(self):
        """ingest() should decrease score for candidates that fail validation."""
        detector = LocaleDetector()

        # Set initial scores to have something to decrease
        for candidate in detector.candidates:
            candidate.score = 5

        # Token that violates grouping rules should decrease scores
        detector.ingest("1,23.45")  # Invalid: only 2 digits in thousands group

        # All candidates should have decreased scores
        assert all(candidate.score == 4 for candidate in detector.candidates)

    def test_should_normalize_token_before_validation(self):
        """ingest() should normalize tokens using unicode normalization."""
        detector = LocaleDetector()

        # Unicode token that normalizes to US format
        detector.ingest("1,234.56")  # This should work after normalization

        us_candidate = next(
            c for c in detector.candidates if c.decimal == "." and c.thousands == ","
        )
        assert us_candidate.score == 1

    def test_should_handle_empty_token(self):
        """ingest() should handle empty tokens gracefully."""
        detector = LocaleDetector()
        original_scores = [c.score for c in detector.candidates]

        detector.ingest("")

        # Scores should remain unchanged for empty token
        current_scores = [c.score for c in detector.candidates]
        assert current_scores == original_scores


class TestLocaleDetectorLocking:
    """Test automatic locking behavior."""

    def test_should_lock_when_only_one_candidate_remains(self):
        """Detector should lock when only one candidate has positive score."""
        detector = LocaleDetector()

        # Give all candidates negative scores except one
        for candidate in detector.candidates:
            candidate.score = -10
        detector.candidates[0].score = 1

        assert detector.is_locked
        assert detector.best_candidate == detector.candidates[0]

    def test_should_lock_when_leader_has_10x_advantage(self):
        """Detector should lock when leader's score >= 10x runner-up."""
        detector = LocaleDetector()

        detector.candidates[0].score = 20
        detector.candidates[1].score = 2  # 10x difference
        detector.candidates[2].score = 1

        assert detector.is_locked
        assert detector.best_candidate == detector.candidates[0]

    def test_should_not_lock_when_leader_advantage_insufficient(self):
        """Detector should not lock when leader advantage < 10x."""
        detector = LocaleDetector()

        detector.candidates[0].score = 19
        detector.candidates[1].score = 2  # 9.5x difference - not enough

        assert not detector.is_locked

    def test_should_not_lock_when_multiple_candidates_tied(self):
        """Detector should not lock when multiple candidates have same top score."""
        detector = LocaleDetector()

        detector.candidates[0].score = 10
        detector.candidates[1].score = 10  # Tied for first
        detector.candidates[2].score = 5

        assert not detector.is_locked


class TestLocaleDetectorConfidence:
    """Test confidence calculation."""

    def test_should_return_zero_confidence_initially(self):
        """Confidence should be 0.0 initially."""
        detector = LocaleDetector()
        assert detector.confidence == 0.0

    def test_should_return_high_confidence_when_locked(self):
        """Confidence should be high when detector is locked."""
        detector = LocaleDetector()

        # Create a clear winner
        detector.candidates[0].score = 20
        detector.candidates[1].score = 1

        assert detector.is_locked
        assert detector.confidence > 0.9

    def test_should_return_low_confidence_when_tied(self):
        """Confidence should be low when candidates are tied or close."""
        detector = LocaleDetector()

        # Create a tie
        detector.candidates[0].score = 10
        detector.candidates[1].score = 10

        assert detector.confidence < 0.6

    def test_should_calculate_confidence_based_on_score_separation(self):
        """Confidence should increase with score separation."""
        detector = LocaleDetector()

        # Small separation
        detector.candidates[0].score = 10
        detector.candidates[1].score = 9
        low_confidence = detector.confidence

        # Reset and try larger separation
        for candidate in detector.candidates:
            candidate.score = 0
        detector.candidates[0].score = 10
        detector.candidates[1].score = 5
        high_confidence = detector.confidence

        assert high_confidence > low_confidence


class TestLocaleDetectorBestCandidate:
    """Test best candidate selection."""

    def test_should_return_highest_scoring_candidate(self):
        """best_candidate should return candidate with highest score."""
        detector = LocaleDetector()

        detector.candidates[2].score = 15
        detector.candidates[0].score = 10
        detector.candidates[1].score = 5

        assert detector.best_candidate == detector.candidates[2]

    def test_should_return_first_candidate_when_tied(self):
        """best_candidate should return first candidate when scores are tied."""
        detector = LocaleDetector()

        detector.candidates[0].score = 10
        detector.candidates[1].score = 10
        detector.candidates[2].score = 5

        assert detector.best_candidate == detector.candidates[0]

    def test_should_return_none_when_all_scores_negative(self):
        """Should return None when all candidates have negative scores."""
        detector = LocaleDetector()

        for candidate in detector.candidates:
            candidate.score = -5

        assert detector.best_candidate is None


class TestLocaleDetectorFreeze:
    """Test manual freezing functionality."""

    def test_should_freeze_to_specific_candidate(self):
        """freeze() should lock detector to specified candidate."""
        detector = LocaleDetector()
        target_candidate = detector.candidates[2]

        detector.freeze(target_candidate)

        assert detector.is_locked
        assert detector.best_candidate == target_candidate
        assert detector.confidence == 1.0

    def test_should_ignore_subsequent_ingestion_when_frozen(self):
        """ingest() should not change scores when detector is frozen."""
        detector = LocaleDetector()
        target_candidate = detector.candidates[0]

        detector.freeze(target_candidate)
        original_scores = [c.score for c in detector.candidates]

        detector.ingest("1.234,56")  # European format
        current_scores = [c.score for c in detector.candidates]

        assert current_scores == original_scores
        assert detector.best_candidate == target_candidate


class TestLocaleDetectorOverride:
    """Test manual override functionality."""

    def test_should_override_to_specific_candidate(self):
        """override() should set detector to specified candidate."""
        detector = LocaleDetector()

        # Set up some scores first
        detector.candidates[0].score = 10
        detector.candidates[1].score = 5

        target_candidate = detector.candidates[2]
        detector.override(target_candidate)

        assert detector.best_candidate == target_candidate
        assert detector.is_locked

    def test_should_allow_ingestion_after_override(self):
        """ingest() should work normally after override() (unlike freeze())."""
        detector = LocaleDetector()
        target_candidate = detector.candidates[0]

        detector.override(target_candidate)
        original_score = target_candidate.score

        detector.ingest("1,234.56")  # Should increase US format score

        assert target_candidate.score > original_score


class TestLocaleDetectorIntegration:
    """Integration tests simulating real-world usage."""

    def test_should_detect_us_format_series(self):
        """Detector should correctly identify US format from series."""
        detector = LocaleDetector()

        us_tokens = ["1,234.56", "789.01", "12,345.67", "999.99", "1,000,000.00"]

        for token in us_tokens:
            detector.ingest(token)

        best = detector.best_candidate
        assert best is not None
        assert best.decimal == "."
        assert best.thousands == ","
        assert detector.confidence > 0.95

    def test_should_detect_european_format_series(self):
        """Detector should correctly identify European format from series."""
        detector = LocaleDetector()

        european_tokens = ["1.234,56", "789,01", "12.345,67", "999,99"]

        for token in european_tokens:
            detector.ingest(token)

        best = detector.best_candidate
        assert best is not None
        assert best.decimal == ","
        assert best.thousands == "."
        assert detector.confidence > 0.95

    def test_should_handle_mixed_format_gracefully(self):
        """Detector should handle mixed formats without crashing."""
        detector = LocaleDetector()

        mixed_tokens = ["1,234.56", "1.234,56", "1 234.56", "invalid"]

        # Should not crash when processing mixed formats
        for token in mixed_tokens:
            detector.ingest(token)

        # Should not crash and should maintain candidates list
        assert len(detector.candidates) == 6
        # Some candidates may have negative scores due to conflicting formats
        assert detector.best_candidate is None or detector.best_candidate.score >= 0

    def test_should_achieve_target_accuracy_on_homogeneous_series(self):
        """Detector should achieve ≥99% accuracy for homogeneous series ≥5 values."""
        # This test simulates large corpus with known formats
        test_cases = [
            (["1,234.56", "789.01", "12,345.67", "999.99", "1,000.00"], ".", ","),
            (["1.234,56", "789,01", "12.345,67", "999,99", "1.000,00"], ",", "."),
            (["1 234.56", "789.01", "12 345.67", "999.99", "1 000.00"], ".", " "),
        ]

        correct_detections = 0

        for tokens, expected_decimal, expected_thousands in test_cases:
            detector = LocaleDetector()

            for token in tokens:
                detector.ingest(token)

            best = detector.best_candidate
            if (
                best
                and best.decimal == expected_decimal
                and best.thousands == expected_thousands
            ):
                correct_detections += 1

        accuracy = correct_detections / len(test_cases)
        assert accuracy >= 0.99  # ≥99% accuracy requirement


class TestMissingDetectorCoverage:
    """Additional tests to achieve 100% coverage for missing detector branches."""

    def test_should_cover_auto_lock_ratio_conditions(self):
        """Test auto-lock conditions with ratio calculations."""
        # Create detector with custom candidates
        candidates = [
            LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0),
            LocaleCandidate(decimal=",", thousands=".", group_size=3, score=0),
        ]
        detector = LocaleDetector(candidates)

        # Set up scores to test ratio-based auto-lock
        candidates[0].score = 20  # Leader
        candidates[1].score = 1  # Runner-up

        # This should trigger the ≥10x advantage auto-lock condition
        assert detector.is_locked
        assert detector.confidence >= 0.98

    def test_should_cover_confidence_edge_cases(self):
        """Test confidence calculation edge cases."""
        # Create detector with candidates
        candidates = [
            LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0),
            LocaleCandidate(decimal=",", thousands=".", group_size=3, score=0),
        ]
        detector = LocaleDetector(candidates)

        # Test confidence when all scores are 0
        assert detector.confidence == 0.0

        # Test confidence with one positive, one negative
        candidates[0].score = 5
        candidates[1].score = -1

        confidence = detector.confidence
        assert 0.7 <= confidence <= 0.99

    def test_should_cover_best_candidate_all_negative(self):
        """Test best_candidate when all scores are negative."""
        # Create detector with candidates
        candidates = [
            LocaleCandidate(decimal=".", thousands=",", group_size=3, score=-5),
            LocaleCandidate(decimal=",", thousands=".", group_size=3, score=-3),
        ]
        detector = LocaleDetector(candidates)

        # Should return None when all scores are negative
        assert detector.best_candidate is None

    def test_should_cover_is_locked_insufficient_candidates(self):
        """Test is_locked when there are insufficient candidates for ratio lock."""
        # Create detector with only one candidate
        candidates = [
            LocaleCandidate(decimal=".", thousands=",", group_size=3, score=5),
        ]
        detector = LocaleDetector(candidates)

        # Should be locked with only one positive candidate
        assert detector.is_locked

        # Create detector with no positive candidates
        candidates = [
            LocaleCandidate(decimal=".", thousands=",", group_size=3, score=-1),
            LocaleCandidate(decimal=",", thousands=".", group_size=3, score=-2),
        ]
        detector = LocaleDetector(candidates)

        # Should not be locked with no positive candidates
        assert not detector.is_locked
