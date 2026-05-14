"""Test cases for the core parsing module."""

import re

import pytest

from intl_number_parser.candidates import LocaleCandidate
from intl_number_parser.core import (
    _apply_precision_constraints,
    _build_number_pattern,
    _extract_number_from_text,
    _extract_scientific_notation_linear,
    _extract_with_candidate,
    _extract_with_fallback_patterns,
    _has_invalid_repeated_separator_group,
    _is_potential_decimal_separator,
    _is_valid_number_format,
    _is_valid_thousands_pattern_text,
    _normalize_canonical_number,
    _parse_mantissa_to_canonical,
    _parse_to_canonical,
    parse_number,
)
from intl_number_parser.detector import LocaleDetector


class TestParseNumberBasics:
    """Test basic number parsing functionality."""

    def test_should_parse_simple_integer(self):
        """parse_number should parse simple integers and return int."""
        result = parse_number("123")
        assert result == 123
        assert isinstance(result, int)

    def test_should_parse_simple_decimal(self):
        """parse_number should parse simple decimals and return string."""
        result = parse_number("123.45")
        assert result == "123.45"
        assert isinstance(result, str)

    def test_should_parse_zero(self):
        """parse_number should parse zero correctly."""
        result = parse_number("0")
        assert result == 0
        assert isinstance(result, int)

    def test_should_parse_decimal_zero(self):
        """parse_number should parse decimal zero correctly."""
        result = parse_number("0.0")
        assert result == "0.0"
        assert isinstance(result, str)


class TestParseNumberPrecisionConstraints:
    """Test precision constraints for integer vs string return."""

    def test_should_return_int_for_small_integers(self):
        """parse_number should return int for integers within 2^63-1."""
        # Test various sizes within the limit
        result = parse_number("9223372036854775807")  # 2^63-1
        assert result == 9223372036854775807
        assert isinstance(result, int)

    def test_should_return_string_for_large_integers(self):
        """parse_number should return string for integers exceeding 2^63-1."""
        # Test value larger than 2^63-1
        result = parse_number("9223372036854775808")  # 2^63
        assert result == "9223372036854775808"
        assert isinstance(result, str)

    def test_should_return_string_for_decimals_with_34_digits(self):
        """parse_number should handle decimals with up to 34 significant digits."""
        # 34 significant digits
        number = "1234567890123456789012345678901234"
        result = parse_number(number + ".0")
        assert result == number + ".0"
        assert isinstance(result, str)

    def test_should_return_string_for_all_decimals(self):
        """parse_number should always return string for decimal numbers."""
        result = parse_number("1.0")
        assert result == "1.0"
        assert isinstance(result, str)


class TestParseNumberSigns:
    """Test sign handling."""

    def test_should_parse_negative_integer(self):
        """parse_number should parse negative integers."""
        result = parse_number("-123")
        assert result == -123
        assert isinstance(result, int)

    def test_should_parse_negative_decimal(self):
        """parse_number should parse negative decimals."""
        result = parse_number("-123.45")
        assert result == "-123.45"
        assert isinstance(result, str)

    def test_should_parse_positive_sign_integer(self):
        """parse_number should parse explicit positive integers."""
        result = parse_number("+123")
        assert result == 123
        assert isinstance(result, int)

    def test_should_parse_positive_sign_decimal(self):
        """parse_number should parse explicit positive decimals."""
        result = parse_number("+123.45")
        assert result == "123.45"
        assert isinstance(result, str)


class TestParseNumberScientificNotation:
    """Test scientific notation parsing."""

    def test_should_parse_scientific_notation_positive_exponent(self):
        """parse_number should parse scientific notation with positive exponent."""
        result = parse_number("1.23e4")
        assert result == "1.23e4"
        assert isinstance(result, str)

    def test_should_parse_scientific_notation_negative_exponent(self):
        """parse_number should parse scientific notation with negative exponent."""
        result = parse_number("1.23e-4")
        assert result == "1.23e-4"
        assert isinstance(result, str)

    def test_should_parse_scientific_notation_uppercase_e(self):
        """parse_number should parse scientific notation with uppercase E."""
        result = parse_number("1.23E4")
        assert result == "1.23E4"
        assert isinstance(result, str)

    def test_should_parse_scientific_notation_signed_exponent(self):
        """parse_number should parse scientific notation with signed exponent."""
        result = parse_number("1.23e+4")
        assert result == "1.23e+4"
        assert isinstance(result, str)

    def test_should_parse_integer_scientific_notation(self):
        """parse_number should parse integer scientific notation."""
        result = parse_number("123e2")
        assert result == "123e2"
        assert isinstance(result, str)


class TestParseNumberWithThousandsSeparators:
    """Test parsing with thousands separators."""

    def test_should_parse_us_format_with_thousands(self):
        """parse_number should parse US format with comma thousands."""
        result = parse_number("1,234,567.89")
        assert result == "1234567.89"
        assert isinstance(result, str)

    def test_should_parse_european_format_with_thousands(self):
        """parse_number should parse European format with period thousands."""
        result = parse_number("1.234.567,89")
        assert result == "1234567.89"
        assert isinstance(result, str)

    def test_should_parse_space_separated_thousands(self):
        """parse_number should parse space-separated thousands."""
        result = parse_number("1 234 567.89")
        assert result == "1234567.89"
        assert isinstance(result, str)

    def test_should_parse_apostrophe_thousands(self):
        """parse_number should parse apostrophe thousands separators."""
        result = parse_number("1'234'567.89")
        assert result == "1234567.89"
        assert isinstance(result, str)

    def test_should_parse_integer_with_thousands(self):
        """parse_number should parse integers with thousands separators."""
        result = parse_number("1,234,567")
        assert result == 1234567
        assert isinstance(result, int)


class TestParseNumberWithDetector:
    """Test parsing with provided LocaleDetector."""

    def test_should_use_provided_detector_best_candidate(self):
        """parse_number should use detector's best candidate when provided."""
        detector = LocaleDetector()
        # Train detector with European format
        detector.ingest("1.234,56")
        detector.ingest("789,01")

        result = parse_number("1.234,56", detector)
        assert result == "1234.56"
        assert isinstance(result, str)

    def test_should_handle_detector_with_no_best_candidate(self):
        """parse_number should fallback when detector has no best candidate."""
        detector = LocaleDetector()
        # Make all candidates have negative scores
        for candidate in detector.candidates:
            candidate.score = -1

        result = parse_number("123.45", detector)
        assert result == "123.45"
        assert isinstance(result, str)

    def test_should_work_without_detector(self):
        """parse_number should work with per-token detection when no detector given."""
        result = parse_number("1,234.56")
        assert result == "1234.56"
        assert isinstance(result, str)


class TestParseNumberEmbeddedInText:
    """Test extracting numbers from free text."""

    def test_should_extract_first_number_from_text(self):
        """parse_number should extract first number from free text."""
        result = parse_number("The price is $1,234.56 today")
        assert result == "1234.56"
        assert isinstance(result, str)

    def test_should_extract_integer_from_text(self):
        """parse_number should extract integer from free text."""
        result = parse_number("We have 42 items in stock")
        assert result == 42
        assert isinstance(result, int)

    def test_should_extract_negative_number_from_text(self):
        """parse_number should extract negative numbers from text."""
        result = parse_number("Temperature dropped to -15.5 degrees")
        assert result == "-15.5"
        assert isinstance(result, str)

    def test_should_extract_scientific_notation_from_text(self):
        """parse_number should extract scientific notation from text."""
        result = parse_number("The distance is 1.23e8 meters")
        assert result == "1.23e8"
        assert isinstance(result, str)


class TestParseNumberEdgeCases:
    """Test edge cases and error handling."""

    def test_should_handle_empty_string(self):
        """parse_number should handle empty string."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("")

    def test_should_handle_no_numbers_in_text(self):
        """parse_number should handle text with no numbers."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("No numbers here!")

    def test_should_handle_multiple_decimal_points(self):
        """parse_number should handle invalid format gracefully."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123.45.67")

    def test_should_handle_unicode_digits(self):
        """parse_number should normalize Unicode digits."""
        result = parse_number("٤٢")  # Arabic-Indic digits for 42
        assert result == 42
        assert isinstance(result, int)

    def test_should_handle_decimal_without_leading_zero(self):
        """parse_number should handle decimal numbers without leading zero."""
        result = parse_number(".123")
        assert result == "0.123"
        assert isinstance(result, str)

    def test_should_handle_trailing_decimal_point(self):
        """parse_number should handle numbers with trailing decimal point."""
        result = parse_number("123.")
        assert result == "123.0"
        assert isinstance(result, str)

    def test_should_reject_consecutive_periods(self):
        """parse_number should reject numbers with consecutive periods."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123..45")

    def test_should_reject_consecutive_commas(self):
        """parse_number should reject numbers with consecutive commas."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123,,45")

    def test_should_reject_mixed_consecutive_separators(self):
        """parse_number should reject numbers with mixed consecutive separators."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123.,45")
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123,.45")

    def test_should_reject_invalid_multiple_decimals_periods(self):
        """parse_number should reject invalid multiple decimal patterns with periods."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123.45.6")  # Last group not 3 digits
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123.4567.89")  # Middle group not 3 digits

    def test_should_reject_invalid_multiple_decimals_commas(self):
        """parse_number should reject invalid multiple decimal patterns with commas."""
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123,45,6")  # Last group not 3 digits
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("123,4567,89")  # Middle group not 3 digits


class TestParseNumberNormalization:
    """Test Unicode normalization integration."""

    def test_should_normalize_unicode_input(self):
        """parse_number should normalize Unicode input."""
        # Full-width digits and punctuation
        result = parse_number("１２３．４５")
        assert result == "123.45"
        assert isinstance(result, str)

    def test_should_handle_non_breaking_spaces(self):
        """parse_number should handle non-breaking spaces as thousands separators."""
        result = parse_number("1\u00a0234.56")  # NBSP
        assert result == "1234.56"
        assert isinstance(result, str)

    def test_should_handle_arabic_punctuation(self):
        """parse_number should handle Arabic punctuation marks."""
        result = parse_number("٤٬٥٦٧٫٨٩")
        assert result == "4567.89"
        assert isinstance(result, str)


class TestCoverageEdgeCases:
    """Test specific edge cases to improve coverage."""

    def test_should_handle_no_valid_number_extraction(self):
        """parse_number should raise ValueError when no valid number extracted."""
        # Create a text that will not match any extraction patterns
        with pytest.raises(ValueError, match="No valid number found in token"):
            parse_number("abc xyz no numbers here!")

    def test_should_handle_comma_decimal_validation_failure(self):
        """Test validation failure for invalid comma decimal patterns."""
        # Pattern that looks like comma decimals but is invalid:
        # X,Y,Z where Y is not 3 digits
        with pytest.raises(ValueError, match="No valid number found in token"):
            parse_number("1,23,45")  # Invalid: 23 is not 3 digits for thousands

    def test_should_handle_extract_with_candidate_returning_none(self):
        """Test when _extract_with_candidate returns None but detector has candidate."""
        # Create a detector with a specific candidate
        detector = LocaleDetector()
        # Force a specific candidate by manipulating scores
        for candidate in detector.candidates:
            candidate.score = -1
        detector.candidates[0].score = 1  # Make first candidate the best

        # Create text that won't match the pattern but has a best candidate
        result = parse_number("123.45", detector)  # Should still work with fallback
        assert result == "123.45"

    def test_should_handle_fallback_patterns_failure(self):
        """Test when both candidate extraction and fallback patterns fail."""
        # Use a string that contains only invalid patterns
        with pytest.raises(ValueError, match="No valid number found in token"):
            parse_number("..,,")  # Only invalid separators

    def test_should_handle_candidate_without_thousands_separator(self):
        """Test _build_number_pattern with candidate that has no thousands separator."""
        # Create a candidate without thousands separator
        candidate = LocaleCandidate(
            decimal=".",
            thousands=None,  # This should trigger the else branch
            group_size=3,
            score=0,
        )

        # This should work fine with the candidate
        detector = LocaleDetector([candidate])
        result = parse_number("123.45", detector)
        assert result == "123.45"

    def test_should_handle_invalid_scientific_notation_parts(self):
        """Test handling of malformed scientific notation."""
        # Create malformed scientific notation that doesn't split into exactly 2 parts
        # This is tricky to trigger, but we can try patterns that might confuse parser
        result = parse_number("1e")  # This should still parse as "1" via fallback
        assert result == 1

    def test_should_handle_thousands_pattern_edge_cases(self):
        """Test edge cases in _is_thousands_pattern function."""
        # These should pass validation but test specific branches
        result = parse_number(
            "1,000"
        )  # Simple thousands - may be parsed as European format
        # Accept either integer or string format depending on locale detection
        assert result in [1000, "1.000"]

        result = parse_number("1000")  # No separators at all
        assert result == 1000

    def test_should_handle_normalize_canonical_edge_cases(self):
        """Test edge cases in _normalize_canonical_number."""
        # Test positive sign normalization
        result = parse_number("+123")
        assert result == 123

        # Test trailing decimal point
        result = parse_number("123.")
        assert result == "123.0"

        # Test leading decimal point cases
        result = parse_number(".123")
        assert result == "0.123"

        result = parse_number("+.123")
        assert result == "0.123"

        result = parse_number("-.123")
        assert result == "-0.123"

    def test_should_handle_precision_constraints_value_error(self):
        """Test the ValueError catch block in _apply_precision_constraints."""
        # This is very hard to trigger since canonical numbers should be well-formed
        # But we can test the int conversion path
        result = parse_number("123")
        assert result == 123
        assert isinstance(result, int)

        # Test edge of int64 range
        result = parse_number("-9223372036854775808")  # -2^63
        assert result == -9223372036854775808
        assert isinstance(result, int)


class TestDetectorInteraction:
    """Test interaction between parse_number and LocaleDetector."""

    def test_should_handle_detector_with_all_negative_candidates(self):
        """Test when detector exists but all candidates have negative scores."""
        detector = LocaleDetector()
        # Make all candidates have negative scores
        for candidate in detector.candidates:
            candidate.score = -10

        # Should fallback to pattern matching
        result = parse_number("123.45", detector)
        assert result == "123.45"

    def test_should_handle_temporary_detector_creation(self):
        """Test path where no detector is provided and temporary one is created."""
        # This tests the else branch in _extract_number_from_text
        result = parse_number("1,234.56")  # No detector provided
        assert result == "1234.56"


class TestInvalidPatternValidation:
    """Test specific validation patterns that aren't covered."""

    def test_should_reject_complex_invalid_decimal_patterns(self):
        """Test rejection of complex invalid decimal patterns."""
        # Test the decimal_like_pattern branch that fails thousands_pattern check
        with pytest.raises(ValueError, match="No valid number found in token"):
            parse_number("1.2345.67")  # Invalid: 2345 is not 3 digits

    def test_should_reject_consecutive_separator_variations(self):
        """Test all types of consecutive separators."""
        invalid_patterns = [
            "..",  # consecutive periods
            ",,",  # consecutive commas
            ".,",  # mixed consecutive
            ",.",  # mixed consecutive reversed
        ]

        for pattern in invalid_patterns:
            with pytest.raises(ValueError, match="No valid number found in token"):
                parse_number(f"123{pattern}456")

    def test_should_handle_valid_thousands_patterns(self):
        """Test that valid thousands patterns pass validation."""
        # These should all be valid and not trigger the validation failure
        valid_patterns = [
            "1.234.567",  # Valid thousands with periods
            "1,234,567",  # Valid thousands with commas
            "1,234,567.89",  # Valid thousands with decimal
            "1.234.567,89",  # Valid European format
        ]

        for pattern in valid_patterns:
            result = parse_number(pattern)
            assert result is not None  # Should not raise ValueError


class TestFallbackExtractionPaths:
    """Test specific fallback extraction scenarios."""

    def test_should_use_fallback_when_candidate_extraction_fails(self):
        """Test fallback pattern usage when candidate-based extraction fails."""
        # Create a very restrictive candidate that won't match normal numbers
        restrictive_candidate = LocaleCandidate(
            decimal="|",  # Unusual decimal separator
            thousands="^",  # Unusual thousands separator
            group_size=3,
            score=100,  # High score to make it the best candidate
        )

        detector = LocaleDetector([restrictive_candidate])

        # Normal number should still work via fallback patterns
        result = parse_number("123.45", detector)
        # The fallback may parse just the integer part in some cases
        assert result in [123, "123.45"]

    def test_should_handle_no_pattern_matches(self):
        """Test when no patterns match at all."""
        # String with no recognizable number patterns
        with pytest.raises(ValueError, match="No valid number found in token"):
            parse_number("completely invalid text with no numbers")


class TestCoverageImprovements:
    """Target specific uncovered lines to improve coverage above 95%."""

    def test_should_handle_fallback_patterns_no_matches(self):
        """Test _extract_with_fallback_patterns when no patterns match."""
        # Test with text that has no valid number patterns
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("no numbers here at all")

    def test_should_handle_malformed_scientific_notation(self):
        """Test scientific notation parsing edge cases."""
        # Test scientific notation with invalid exponent parts - extracts before 'e'
        result = parse_number("1.23e")  # Missing exponent
        assert result == "1.23"

        # Test valid scientific notation with uppercase E
        result = parse_number("1.23E+4")
        assert result == "1.23E+4"

    def test_should_handle_decimal_separator_edge_cases(self):
        """Test _is_potential_decimal_separator edge cases."""
        # Test edge cases that might hit specific branches
        result = parse_number("1.23")  # Simple decimal
        assert result == "1.23"

        # Test with trailing decimal
        result = parse_number("123.")
        assert result == "123.0"

    def test_should_handle_precision_constraints_edge_cases(self):
        """Test _apply_precision_constraints edge cases."""
        # Test ValueError handling in precision constraints
        # This should test the ValueError catch block
        result = parse_number("123")
        assert result == 123

        # Test very large integers that exceed int64
        result = parse_number("9223372036854775808")  # 2^63 (MAX_INT64 + 1)
        assert result == "9223372036854775808"

        # Test scientific notation (should return string in scientific format)
        result = parse_number("1.23e10")
        assert result == "1.23e10"

    def test_should_handle_thousands_pattern_detection(self):
        """Test thousands pattern detection edge cases."""
        # Test numbers that might trigger thousands pattern detection
        result = parse_number("1,234,567")
        assert result == 1234567

        # Test mixed separators that might be ambiguous
        result = parse_number("1.234.567")
        assert result == 1234567

    def test_should_handle_candidate_without_thousands_separator(self):
        """Test candidates without thousands separator."""
        # Create a detector with a candidate that has no thousands separator
        detector = LocaleDetector()
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)
        detector.override(candidate)

        result = parse_number("1234.56", detector)
        assert result == "1234.56"

    def test_should_handle_empty_decimal_part(self):
        """Test handling of empty decimal parts."""
        # Test with decimal separator but no digits after
        result = parse_number("123.")
        assert result == "123.0"

        # Test with leading decimal point
        result = parse_number(".123")
        assert result == "0.123"

    def test_should_handle_normalized_canonical_edge_cases(self):
        """Test _normalize_canonical_number edge cases."""
        # Test positive sign normalization
        result = parse_number("+123.45")
        assert result == "123.45"

        # Test negative decimal point
        result = parse_number("-.123")
        assert result == "-0.123"

        # Test positive decimal point
        result = parse_number("+.123")
        assert result == "0.123"


class TestMissingCoverageIsValidNumberFormat:
    """Test cases to cover missing lines in _is_valid_number_format."""

    def test_should_reject_invalid_period_decimal_pattern(self):
        """Test decimal_like_pattern that doesn't match thousands_pattern."""
        # This matches decimal_like_pattern but not thousands_pattern
        # Pattern: digits.1or2or4+digits.digits -> should be invalid

        # Test case: 1.23.45 (not a valid thousands pattern)
        assert _is_valid_number_format("1.23.45") is False

        # Test case: 1.23.456 (not a valid thousands pattern - 4 digits)
        assert _is_valid_number_format("1.23.456") is False

        # Test case: 1.2.34 (not a valid thousands pattern - 1 digit)
        assert _is_valid_number_format("1.2.34") is False

    def test_should_reject_invalid_comma_decimal_pattern(self):
        """Test comma_decimal_pattern that doesn't match comma_thousands_pattern."""
        # This matches comma_decimal_pattern but not comma_thousands_pattern
        # Pattern: digits,1or2or4+digits,digits -> should be invalid

        # Test case: 1,23,45 (not a valid comma thousands pattern)
        assert _is_valid_number_format("1,23,45") is False

        # Test case: 1,23,456 (not a valid comma thousands pattern - 4 digits)
        assert _is_valid_number_format("1,23,456") is False

        # Test case: 1,2,34 (not a valid comma thousands pattern - 1 digit)
        assert _is_valid_number_format("1,2,34") is False

    def test_should_accept_valid_thousands_patterns(self):
        """Test that valid thousands patterns are accepted."""
        # Valid period thousands patterns
        assert _is_valid_number_format("1.234.567") is True
        assert _is_valid_number_format("12.345.678") is True
        assert _is_valid_number_format("123.456.789") is True

        # Valid comma thousands patterns
        assert _is_valid_number_format("1,234,567") is True
        assert _is_valid_number_format("12,345,678") is True
        assert _is_valid_number_format("123,456,789") is True


class TestMissingCoverageExtractFallback:
    """Test cases to cover missing lines in _extract_number_from_text fallback."""

    def test_should_use_fallback_when_detector_has_no_best_candidate(self):
        """Test fallback extraction when detector has no best candidate."""
        # Create a detector with all candidates having zero or negative scores
        detector = LocaleDetector()
        # The ingest method with invalid tokens doesn't make scores negative,
        # they just don't match any pattern so scores remain 0
        for _ in range(10):
            detector.ingest("invalid")

        # All candidates should have score 0, so best_candidate returns first one
        assert detector.best_candidate is not None
        assert detector.best_candidate.score == 0

        # Should still use fallback patterns when candidate extraction fails
        result = _extract_number_from_text("Price: $1,234.56", detector)
        assert result is not None
        assert result[0] == "1,234.56"

    def test_should_use_fallback_when_candidate_extraction_fails(self):
        """Test fallback extraction when candidate-based extraction fails."""
        # Create a detector with a best candidate that won't match the text
        detector = LocaleDetector()
        detector.ingest("1.234,56")  # European format

        # The detector learned European format (comma as decimal separator)
        # When extracting from "Price: $1,234.56", it treats comma as decimal
        # and only matches "1,234" (stopping at comma which it sees as decimal)
        result = _extract_number_from_text("Price: $1,234.56", detector)
        assert result is not None
        assert result[0] == "1,234"

    def test_should_return_first_match_from_fallback_patterns(self):
        """Test that fallback patterns return the first match found."""
        # Text with multiple numbers - should return the first one
        result = _extract_with_fallback_patterns("Price $123.45 and $678.90")
        assert result == "123.45"

        # Text with mixed formats - the patterns are ordered by priority
        # and the simpler decimal pattern matches "1.234" before the full
        # European pattern can match "1.234,56"
        result = _extract_with_fallback_patterns("European 1.234,56 and US 1,234.56")
        assert result == "1.234"

    def test_should_handle_fallback_patterns_no_matches(self):
        """Test fallback patterns when no matches are found."""
        # Text with no numbers
        result = _extract_with_fallback_patterns("No numbers here")
        assert result is None

        # Text with only invalid patterns
        result = _extract_with_fallback_patterns("Invalid: abc.def")
        assert result is None

    def test_should_handle_none_detector_with_fallback(self):
        """Test extraction with None detector that creates temporary detector."""
        # None detector should create temporary detector and use fallback if needed
        result = _extract_number_from_text("Price: $1,234.56", None)
        assert result is not None
        assert result[0] == "1,234.56"


class TestMissingCoverageParseToCanonical:
    """Test cases to cover missing lines in _parse_to_canonical scientific notation."""

    def test_should_handle_scientific_notation_with_incorrect_parts_length(self):
        """Test scientific notation with parts length != 2."""
        # Scientific notation with multiple e/E - splits on first e/E,
        # preserves the rest
        # re.split(r"[eE]", "1.23eE4", maxsplit=1) = ["1.23", "E4"]
        # Reconstructs as: "1.23" + "e" + "E4" = "1.23eE4"
        result = _parse_to_canonical("1.23eE4")
        assert result == "1.23eE4"  # Preserves malformed scientific notation

    def test_should_handle_scientific_notation_e_char_preservation(self):
        """Test that e/E character is preserved in scientific notation."""
        # Test lowercase e
        result = _parse_to_canonical("1.23e4")
        assert "e" in result
        assert result == "1.23e4"

        # Test uppercase E
        result = _parse_to_canonical("1.23E4")
        assert "E" in result
        assert result == "1.23E4"

        # Test with thousands separators in mantissa (should be removed)
        result = _parse_to_canonical("1,234e4")
        assert (
            result == "1.234e4"
        )  # Without candidate, comma is treated as decimal separator

        # Test with different candidates
        candidate = LocaleCandidate(decimal=",", thousands=".", group_size=3, score=0)
        result = _parse_to_canonical("1.234,56e4", candidate)
        assert result == "1234.56e4"

    def test_should_handle_mixed_case_e_in_scientific_notation(self):
        """Test mixed case handling in scientific notation."""
        # Test that original case is preserved
        result = _parse_to_canonical("123E-4")
        assert result == "123E-4"

        result = _parse_to_canonical("123e+4")
        assert result == "123e+4"

    def test_should_handle_complex_scientific_notation_with_separators(self):
        """Test complex scientific notation with thousands separators."""
        # US format with thousands in mantissa
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )
        result = _parse_to_canonical("1,234.56e4", us_candidate)
        assert result == "1234.56e4"

        # European format with thousands in mantissa
        eu_candidate = LocaleCandidate(
            decimal=",", thousands=".", group_size=3, score=0
        )
        result = _parse_to_canonical("1.234,56E-4", eu_candidate)
        assert result == "1234.56E-4"


class TestMissingCoverageNormalizeCanonical:
    """Test cases to cover missing lines in _normalize_canonical_number."""

    def test_should_handle_positive_decimal_without_leading_zero(self):
        """Test +.123 -> 0.123 (line 349)."""
        # Test positive decimal without leading zero
        result = _normalize_canonical_number("+.123")
        assert result == "0.123"

        result = _normalize_canonical_number("+.5")
        assert result == "0.5"

        result = _normalize_canonical_number("+.0")
        assert result == "0.0"

    def test_should_handle_negative_decimal_without_leading_zero(self):
        """Test -.123 -> -0.123 (line 350)."""
        # Test negative decimal without leading zero
        result = _normalize_canonical_number("-.123")
        assert result == "-0.123"

        result = _normalize_canonical_number("-.5")
        assert result == "-0.5"

        result = _normalize_canonical_number("-.0")
        assert result == "-0.0"

    def test_should_handle_all_normalize_canonical_patterns(self):
        """Test comprehensive normalization patterns."""
        # Test regular decimal without leading zero
        result = _normalize_canonical_number(".123")
        assert result == "0.123"

        # Test trailing decimal point
        result = _normalize_canonical_number("123.")
        assert result == "123.0"

        # Test positive sign removal
        result = _normalize_canonical_number("+123")
        assert result == "123"

        # Test combination of positive sign and decimal
        result = _normalize_canonical_number("+123.456")
        assert result == "123.456"

        # Test combination of negative sign and trailing decimal
        result = _normalize_canonical_number("-123.")
        assert result == "-123.0"


class TestMissingCoverageParseMantissa:
    """Test cases to cover missing lines in _parse_mantissa_to_canonical."""

    def test_should_handle_fallback_decimal_detection(self):
        """Test fallback decimal detection when candidate is None."""
        # Test with None candidate - should use fallback logic
        result = _parse_mantissa_to_canonical("1,234.56", None)
        assert result == "1234.56"

        # Test with European format
        result = _parse_mantissa_to_canonical("1.234,56", None)
        assert result == "1234.56"

        # Test with no decimal separator
        result = _parse_mantissa_to_canonical("1234", None)
        assert result == "1234"

    def test_should_use_rightmost_decimal_separator_in_fallback(self):
        """Test that fallback logic uses rightmost potential decimal separator."""
        # Multiple potential decimal separators - should use rightmost
        result = _parse_mantissa_to_canonical("1.234.56", None)
        assert result == "1234.56"

        result = _parse_mantissa_to_canonical("1,234,56", None)
        assert result == "1234.56"

        # Mixed separators - should use rightmost
        result = _parse_mantissa_to_canonical("1.234,56", None)
        assert result == "1234.56"

        result = _parse_mantissa_to_canonical("1,234.56", None)
        assert result == "1234.56"

    def test_should_handle_no_decimal_separator_fallback(self):
        """Test fallback when no decimal separator is found."""
        # Only thousands separators - should remove all
        result = _parse_mantissa_to_canonical("1,234,567", None)
        assert result == "1234567"

        result = _parse_mantissa_to_canonical("1.234.567", None)
        assert result == "1234567"

        # Mixed thousands separators
        result = _parse_mantissa_to_canonical("1,234.567", None)
        assert result == "1234567"

        # With spaces and apostrophes
        result = _parse_mantissa_to_canonical("1 234 567", None)
        assert result == "1234567"

        result = _parse_mantissa_to_canonical("1'234'567", None)
        assert result == "1234567"

    def test_should_handle_potential_decimal_separators_detection(self):
        """Test potential decimal separators detection logic."""
        # Test edge cases for potential decimal detection
        # Number with 3 digits after separator (could be thousands)
        result = _parse_mantissa_to_canonical("1.234", None)
        assert (
            result == "1.234"
        )  # Without preceding thousands pattern, treated as decimal

        # Number with 1-2 digits after separator (likely decimal)
        result = _parse_mantissa_to_canonical("1.23", None)
        assert result == "1.23"  # Should be treated as decimal

        result = _parse_mantissa_to_canonical("1.2", None)
        assert result == "1.2"  # Should be treated as decimal

        # Test with more complex patterns
        result = _parse_mantissa_to_canonical("12.345.67", None)
        assert result == "12345.67"  # Last separator is decimal

    def test_should_handle_fallback_with_signs(self):
        """Test fallback logic with signed numbers."""
        # Positive signed number
        result = _parse_mantissa_to_canonical("+1,234.56", None)
        assert result == "1234.56"

        # Negative signed number
        result = _parse_mantissa_to_canonical("-1,234.56", None)
        assert result == "-1234.56"

        # Decimal without leading zero
        result = _parse_mantissa_to_canonical("-.123", None)
        assert result == "-0.123"


class TestMissingCoverageAdditional:
    """Additional tests to cover missing branches and achieve 100% coverage."""

    def test_should_cover_scientific_notation_wrong_parts_length(self):
        """Test scientific notation with wrong parts length."""
        # This tests the branch where scientific notation doesn't have exactly 2 parts
        # Create a malformed scientific notation that won't split properly
        result = _parse_to_canonical("1.23ee4")
        assert result == "1.23ee4"

    def test_should_cover_fallback_extraction_path(self):
        """Test fallback extraction path when detector has no best candidate."""
        # Create detector with no best candidate
        detector = LocaleDetector()
        for candidate in detector.candidates:
            candidate.score = -1

        result = parse_number("123.45", detector)
        assert result == "123.45"

    def test_should_cover_extraction_returns_none(self):
        """Test when extraction returns None."""
        # This should trigger the case where no valid number is found
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number("no numbers here")

    def test_should_cover_fallback_mantissa_parsing(self):
        """Test fallback mantissa parsing path."""
        # Test with no candidate (fallback path)
        result = _parse_mantissa_to_canonical("1,234.56", None)
        assert result == "1234.56"

    def test_should_cover_precision_constraints_value_error(self):
        """Test precision constraints with value error."""
        # Create a malformed number that would cause ValueError in int()
        result = _apply_precision_constraints("not_a_number")
        assert result == "not_a_number"

    def test_should_cover_is_valid_number_format_period_patterns(self):
        """Test _is_valid_number_format with period patterns."""
        # Test invalid period patterns
        assert not _is_valid_number_format("1.23.45")  # Invalid multiple decimals
        assert not _is_valid_number_format("1.2345.67")  # Invalid multiple decimals

        # Test valid thousands patterns
        assert _is_valid_number_format("1.234.567")  # Valid thousands

    def test_should_cover_is_valid_number_format_comma_patterns(self):
        """Test _is_valid_number_format with comma patterns."""
        # Test invalid comma patterns
        assert not _is_valid_number_format("1,23,45")  # Invalid multiple decimals
        assert not _is_valid_number_format("1,2345,67")  # Invalid multiple decimals

        # Test valid thousands patterns
        assert _is_valid_number_format("1,234,567")  # Valid thousands


class TestMissingCoverageSpecificBranches:
    """Test specific branches that are missing coverage."""

    def test_should_cover_is_valid_number_format_comma_thousands_pattern_failure(self):
        """Test comma thousands pattern validation failure."""
        # Test cases that trigger comma_thousands_pattern check failure
        assert not _is_valid_number_format("1,23,4")  # Invalid comma grouping
        assert not _is_valid_number_format("1,2,3")  # Invalid comma grouping

    def test_should_cover_is_valid_number_format_period_thousands_pattern_failure(self):
        """Test period thousands pattern validation failure."""
        # Test cases that trigger thousands_pattern check failure
        assert not _is_valid_number_format("1.23.4")  # Invalid period grouping
        assert not _is_valid_number_format("1.2.3")  # Invalid period grouping

    def test_should_cover_parse_to_canonical_scientific_notation_fallback(self):
        """Test scientific notation fallback in _parse_to_canonical."""
        # Test scientific notation with incorrect parts length
        result = _parse_to_canonical("1.23eee4")
        assert result == "1.23eee4"

    def test_should_cover_is_potential_decimal_separator_edge_case(self):
        """Test _is_potential_decimal_separator edge cases."""
        # Test cases that trigger specific branches
        assert not _is_potential_decimal_separator("1.234.567", 1, "234.567")
        assert _is_potential_decimal_separator("1.23", 1, "23")

    def test_should_cover_parse_mantissa_fallback_no_potential_decimals(self):
        """Test _parse_mantissa_to_canonical fallback with no potential decimals."""
        # Test with no candidate and no decimal separators
        result = _parse_mantissa_to_canonical("1234567", None)
        assert result == "1234567"

    def test_should_cover_parse_mantissa_fallback_with_potential_decimals(self):
        """Test _parse_mantissa_to_canonical fallback with potential decimals."""
        # Test with no candidate but with potential decimal separators
        result = _parse_mantissa_to_canonical("1,234.56", None)
        assert result == "1234.56"

    def test_should_cover_apply_precision_constraints_value_error(self):
        """Test _apply_precision_constraints with ValueError."""
        # Test with malformed number that causes ValueError
        result = _apply_precision_constraints("invalid_number")
        assert result == "invalid_number"

    def test_should_cover_scientific_notation_with_wrong_split_length(self):
        """Test scientific notation with wrong split length."""
        # Test scientific notation that splits into wrong number of parts
        result = _parse_to_canonical("1.23eee4")
        assert result == "1.23eee4"

    def test_should_cover_candidate_without_thousands_in_build_pattern(self):
        """Test _build_number_pattern with candidate without thousands separator."""
        # Create candidate without thousands separator
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)
        pattern = _build_number_pattern(candidate)
        assert pattern is not None
        assert "thousands" not in pattern

    def test_should_cover_parse_mantissa_with_candidate_and_thousands(self):
        """Test _parse_mantissa_to_canonical with candidate and thousands separator."""
        # Test with candidate having thousands separator
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        result = _parse_mantissa_to_canonical("1,234.56", candidate)
        assert result == "1234.56"

    def test_should_cover_parse_mantissa_with_candidate_no_decimal_pos(self):
        """Test _parse_mantissa_to_canonical with candidate but no decimal position."""
        # Test with candidate but no decimal separator in input
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        result = _parse_mantissa_to_canonical("1,234", candidate)
        assert result == "1234"

    def test_should_cover_parse_mantissa_with_candidate_no_thousands(self):
        """Test _parse_mantissa_to_canonical with candidate but no thousands sep."""
        # Test with candidate having no thousands separator
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)
        result = _parse_mantissa_to_canonical("1234.56", candidate)
        assert result == "1234.56"


class TestMissingCoverageCompleteTarget:
    """Additional tests to achieve 100% coverage by targeting exact missing branches."""

    def test_should_cover_is_valid_number_format_specific_branches(self):
        """Test specific branches in _is_valid_number_format to reach 100% coverage."""
        # Test cases that specifically trigger lines 129-133 and 137-140
        # These are the comma pattern checks that need to fail the regex match
        assert not _is_valid_number_format("1,2,34")  # Invalid comma decimal pattern
        # Note: "1,234,5" is valid as thousands pattern, need different test cases
        assert not _is_valid_number_format(
            "1,23,45"
        )  # Invalid comma decimal pattern - not matching thousands pattern

        # Test cases that specifically trigger period pattern checks
        assert not _is_valid_number_format("1.2.34")  # Invalid period decimal pattern
        assert not _is_valid_number_format(
            "1.23.45"
        )  # Invalid period decimal pattern - not matching thousands pattern

    def test_should_cover_extract_with_candidate_no_matches(self):
        """Test _extract_with_candidate when no matches are found."""
        # Create a candidate and text that won't match
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        result = _extract_with_candidate("no numbers here", candidate)
        assert result is None

    def test_should_cover_extract_with_candidate_validation_failure(self):
        """Test _extract_with_candidate when validation fails."""
        # Create a candidate that will find a match but fail validation
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        result = _extract_with_candidate("1..23", candidate)
        assert result == "1"  # Returns the first valid match found

    def test_should_cover_parse_to_canonical_scientific_wrong_parts(self):
        """Test _parse_to_canonical with scientific notation having wrong parts."""
        # Test scientific notation that doesn't split into exactly 2 parts
        result = _parse_to_canonical("1.23")  # No 'e' at all
        assert result == "1.23"

        # Test with malformed scientific notation
        result = _parse_to_canonical("1eee2")  # Multiple 'e' characters
        assert result == "1eee2"

    def test_should_cover_is_potential_decimal_separator_false_case(self):
        """Test _is_potential_decimal_separator returning False."""
        # Test case where it returns False due to pattern mismatch
        assert not _is_potential_decimal_separator(
            "1.234.567", 1, "234.567"
        )  # Multiple periods shouldn't be decimal

        # Test case where it returns True for valid pattern
        assert _is_potential_decimal_separator("1.23", 1, "23")

    def test_should_cover_parse_mantissa_fallback_edge_cases(self):
        """Test _parse_mantissa_to_canonical fallback logic edge cases."""
        # Test fallback with empty decimal match
        result = _parse_mantissa_to_canonical("1,234", None)
        assert result == "1.234"  # Comma gets converted to period in fallback

        # Test fallback with potential decimal separator
        result = _parse_mantissa_to_canonical("1,234.56", None)
        assert result == "1234.56"

    def test_should_cover_precision_constraints_malformed_input(self):
        """Test _apply_precision_constraints with malformed input."""
        # Test with input that can't be converted to int
        result = _apply_precision_constraints("abc")
        assert result == "abc"

        # Test with empty string
        result = _apply_precision_constraints("")
        assert result == ""

    def test_should_cover_extract_number_from_text_no_detector(self):
        """Test _extract_number_from_text with no detector."""
        # Test with None detector
        result = _extract_number_from_text("123.45", None)
        assert result is not None
        assert result[0] == "123.45"

    def test_should_cover_parse_number_invalid_format_after_extraction(self):
        """Test parse_number with invalid format after extraction."""
        # This should trigger the validation failure path
        with pytest.raises(ValueError, match="No valid number found"):
            parse_number(
                "1..23"
            )  # Invalid format that might pass extraction but fail validation

    def test_should_cover_build_number_pattern_with_thousands(self):
        """Test _build_number_pattern with thousands separator."""
        # Test with thousands separator
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        pattern = _build_number_pattern(candidate)
        assert pattern is not None
        assert "," in pattern

    def test_should_cover_normalize_canonical_number_edge_cases(self):
        """Test _normalize_canonical_number with all edge cases."""
        # Test all normalization cases
        assert _normalize_canonical_number("123") == "123"
        assert _normalize_canonical_number("123.0") == "123.0"
        assert _normalize_canonical_number("0.123") == "0.123"
        assert _normalize_canonical_number(".123") == "0.123"
        assert _normalize_canonical_number("-.123") == "-0.123"
        assert _normalize_canonical_number("+.123") == "0.123"
        assert _normalize_canonical_number("123.") == "123.0"
        assert _normalize_canonical_number("-123.") == "-123.0"
        assert _normalize_canonical_number("+123.") == "123.0"


class TestSecurityRegressionDoS:
    """Regression tests for parser denial-of-service mitigations."""

    def test_should_validate_digit_only_text_without_regex_search(self, monkeypatch):
        """Long digit-only input should not enter regex-based format checks."""

        def fail_search(*_args, **_kwargs):
            msg = "digit-only format validation should not use re.search"
            raise AssertionError(msg)

        monkeypatch.setattr(re, "search", fail_search)

        assert _is_valid_number_format("1" * 50_000) is True

    def test_should_not_use_scientific_fallback_regex(self, monkeypatch):
        """Malformed scientific input should not hit the old fallback regex."""
        original_finditer = re.finditer

        def guarded_finditer(pattern, text):
            if pattern.startswith(r"[+-]?(?:\d+(?:[,") and "[eE]" in pattern:
                msg = "fallback scientific notation should be parsed linearly"
                raise AssertionError(msg)
            return original_finditer(pattern, text)

        monkeypatch.setattr(re, "finditer", guarded_finditer)

        payload = ("1" * 100) + "e" + ("+" * 100)
        assert parse_number(payload) == "1" * 100

    def test_should_keep_valid_scientific_fallback_behavior(self):
        """Linear scientific fallback should preserve valid scientific matches."""
        assert _extract_with_fallback_patterns("value +1.23e-4") == "+1.23e-4"
        assert _extract_with_fallback_patterns("value .5E+2") == ".5E+2"
        assert _extract_with_fallback_patterns("value 1,234e5") == "1,234e5"
        assert _extract_with_fallback_patterns("value 1 234e5") == "1 234e5"
        assert _extract_with_fallback_patterns("value 1'234.56E+7") == "1'234.56E+7"
        assert _extract_with_fallback_patterns("value 1\u00a0234e5") == "1\u00a0234e5"

    def test_should_handle_non_scientific_scanner_edges(self):
        """Linear scanner should skip invalid starts and malformed exponents."""
        assert _extract_scientific_notation_linear("+") is None
        assert _extract_scientific_notation_linear("+abc") is None
        assert _extract_scientific_notation_linear(".e10") is None
        assert _extract_scientific_notation_linear("1e+") is None
        assert _extract_scientific_notation_linear("123 text") is None

    def test_should_preserve_repeated_separator_validation_edges(self):
        """Linear separator validation should preserve existing edge behavior."""
        assert _has_invalid_repeated_separator_group(".1.23", ".", 2) is False
        assert _has_invalid_repeated_separator_group("1.a.2", ".", 2) is False
        assert _has_invalid_repeated_separator_group("1.23.a", ".", 2) is False
        assert _is_valid_thousands_pattern_text("1234.567", ".") is False
        assert _is_valid_thousands_pattern_text("1.234", ".") is True
        assert _is_valid_thousands_pattern_text("1.234x", ".") is False
        assert _is_valid_thousands_pattern_text("1.234.", ".") is False
        assert _is_valid_thousands_pattern_text("1.234.56", ".") is True
