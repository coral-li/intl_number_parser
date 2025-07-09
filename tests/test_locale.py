"""Tests for locale candidate functionality."""

from intl_number_parser.candidates import (
    COMMON_CANDIDATES,
    LocaleCandidate,
    all_candidates,
)


class TestLocaleCandidateDataclass:
    """Test the LocaleCandidate dataclass structure and behavior."""

    def test_should_create_locale_candidate_with_required_fields(self):
        """Test LocaleCandidate creation with all required fields."""
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)

        assert candidate.decimal == "."
        assert candidate.thousands == ","
        assert candidate.group_size == 3
        assert candidate.score == 0

    def test_should_create_locale_candidate_with_none_thousands(self):
        """Test LocaleCandidate creation with None thousands separator."""
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)

        assert candidate.decimal == "."
        assert candidate.thousands is None
        assert candidate.group_size == 3
        assert candidate.score == 0

    def test_should_allow_mutable_score_updates(self):
        """Test that score field is mutable for evidence accumulation."""
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)

        # Score should be mutable
        candidate.score = 5
        assert candidate.score == 5

        candidate.score += 1
        assert candidate.score == 6

        candidate.score -= 2
        assert candidate.score == 4

    def test_should_support_different_group_sizes(self):
        """Test LocaleCandidate with different group sizes."""
        candidate = LocaleCandidate(
            decimal=".",
            thousands=",",
            group_size=4,  # Some locales use 4-digit groups
            score=0,
        )

        assert candidate.group_size == 4

    def test_should_be_dataclass_instance(self):
        """Test that LocaleCandidate is a proper dataclass."""
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)

        # Should have dataclass attributes
        assert hasattr(candidate, "__dataclass_fields__")
        assert "decimal" in candidate.__dataclass_fields__
        assert "thousands" in candidate.__dataclass_fields__
        assert "group_size" in candidate.__dataclass_fields__
        assert "score" in candidate.__dataclass_fields__


class TestCommonCandidates:
    """Test the COMMON_CANDIDATES list contains all required locale formats."""

    def test_should_contain_six_common_candidates(self):
        """Test COMMON_CANDIDATES contains exactly 6 format variations."""
        assert len(COMMON_CANDIDATES) == 6

    def test_should_contain_us_uk_format(self):
        """Test contains US/UK format: 1,234.56."""
        us_uk = next(
            (c for c in COMMON_CANDIDATES if c.decimal == "." and c.thousands == ","),
            None,
        )
        assert us_uk is not None
        assert us_uk.decimal == "."
        assert us_uk.thousands == ","
        assert us_uk.group_size == 3
        assert us_uk.score == 0

    def test_should_contain_european_format(self):
        """Test contains European format: 1.234,56."""
        european = next(
            (c for c in COMMON_CANDIDATES if c.decimal == "," and c.thousands == "."),
            None,
        )
        assert european is not None
        assert european.decimal == ","
        assert european.thousands == "."
        assert european.group_size == 3
        assert european.score == 0

    def test_should_contain_nbsp_thousands_comma_decimal(self):
        """Test contains NBSP thousands + comma decimal: 1 234,56."""
        nbsp_comma = next(
            (
                c
                for c in COMMON_CANDIDATES
                if c.decimal == "," and c.thousands == "\u00a0"
            ),
            None,
        )
        assert nbsp_comma is not None
        assert nbsp_comma.decimal == ","
        assert nbsp_comma.thousands == "\u00a0"
        assert nbsp_comma.group_size == 3
        assert nbsp_comma.score == 0

    def test_should_contain_space_thousands_dot_decimal(self):
        """Test contains space thousands + dot decimal: 1 234.56."""
        space_dot = next(
            (c for c in COMMON_CANDIDATES if c.decimal == "." and c.thousands == " "),
            None,
        )
        assert space_dot is not None
        assert space_dot.decimal == "."
        assert space_dot.thousands == " "
        assert space_dot.group_size == 3
        assert space_dot.score == 0

    def test_should_contain_swiss_format(self):
        """Test contains Swiss format: 1'234.56."""
        swiss = next(
            (c for c in COMMON_CANDIDATES if c.decimal == "." and c.thousands == "'"),
            None,
        )
        assert swiss is not None
        assert swiss.decimal == "."
        assert swiss.thousands == "'"
        assert swiss.group_size == 3
        assert swiss.score == 0

    def test_should_contain_space_thousands_comma_decimal_variant(self):
        """Test contains space thousands + comma decimal variant: 1 234 567,89."""
        # This should be the same as the NBSP variant but with regular space
        space_comma = next(
            (c for c in COMMON_CANDIDATES if c.decimal == "," and c.thousands == " "),
            None,
        )
        assert space_comma is not None
        assert space_comma.decimal == ","
        assert space_comma.thousands == " "
        assert space_comma.group_size == 3
        assert space_comma.score == 0

    def test_should_have_all_scores_initialized_to_zero(self):
        """Test all candidates start with score = 0."""
        for candidate in COMMON_CANDIDATES:
            assert candidate.score == 0

    def test_should_have_all_group_sizes_as_three(self):
        """Test all common candidates use 3-digit grouping."""
        for candidate in COMMON_CANDIDATES:
            assert candidate.group_size == 3


class TestAllCandidatesFactory:
    """Test the all_candidates() factory method."""

    def test_should_return_fresh_list_with_zero_scores(self):
        """Test all_candidates() returns fresh list with score=0."""
        candidates1 = all_candidates()
        candidates2 = all_candidates()

        # Should be different list instances
        assert candidates1 is not candidates2

        # Should have same length as COMMON_CANDIDATES
        assert len(candidates1) == len(COMMON_CANDIDATES)
        assert len(candidates2) == len(COMMON_CANDIDATES)

        # All scores should be 0
        for candidate in candidates1:
            assert candidate.score == 0
        for candidate in candidates2:
            assert candidate.score == 0

    def test_should_return_independent_instances(self):
        """Test that modifying one list doesn't affect others."""
        candidates1 = all_candidates()
        candidates2 = all_candidates()

        # Modify score in first list
        candidates1[0].score = 10

        # Second list should be unaffected
        assert candidates2[0].score == 0

    def test_should_preserve_original_common_candidates(self):
        """Test that factory doesn't modify the original COMMON_CANDIDATES."""
        original_scores = [c.score for c in COMMON_CANDIDATES]

        candidates = all_candidates()
        candidates[0].score = 15

        # Original should be unchanged
        current_scores = [c.score for c in COMMON_CANDIDATES]
        assert original_scores == current_scores

    def test_should_return_copies_with_same_format_specifications(self):
        """Test that factory returns candidates with same format specs."""
        candidates = all_candidates()

        # Should have same formats as COMMON_CANDIDATES
        for i, candidate in enumerate(candidates):
            original = COMMON_CANDIDATES[i]
            assert candidate.decimal == original.decimal
            assert candidate.thousands == original.thousands
            assert candidate.group_size == original.group_size
            # But score should be reset to 0 (even if original was modified)
            assert candidate.score == 0


class TestLocaleTypes:
    """Test type hints and annotations."""

    def test_should_have_proper_type_annotations(self):
        """Test LocaleCandidate has correct type annotations."""
        annotations = LocaleCandidate.__annotations__

        assert annotations["decimal"] == "str"
        # Note: str | None shows up differently in annotations
        assert "thousands" in annotations
        assert annotations["group_size"] == "int"
        assert annotations["score"] == "int"

    def test_all_candidates_return_type(self):
        """Test all_candidates() returns List[LocaleCandidate]."""
        candidates = all_candidates()
        assert isinstance(candidates, list)

        for candidate in candidates:
            assert isinstance(candidate, LocaleCandidate)
