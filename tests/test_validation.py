"""Tests for validation logic and numeric token parsing."""

from intl_number_parser.candidates import LocaleCandidate
from intl_number_parser.validation import (
    _validate_characters_and_signs,
    _validate_decimal_parts,
    _validate_exponent,
    _validate_integer_part,
    _validate_thousands_groups,
    validate,
)


class TestBasicValidation:
    """Test basic validation scenarios for common number formats."""

    def test_should_validate_simple_integer_us_format(self):
        """Test validation of simple integer in US format."""
        # Test basic integer validation
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("123", candidate) is True

    def test_should_validate_simple_decimal_us_format(self):
        """Test validation of simple decimal number in US format."""
        # Test basic decimal validation
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("123.45", candidate) is True

    def test_should_validate_thousands_groups_us_format(self):
        """Test validation of thousands grouping in US format."""
        # Test proper thousands grouping
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,234", candidate) is True
        assert validate("12,345", candidate) is True
        assert validate("123,456", candidate) is True

    def test_should_validate_thousands_with_decimal_us_format(self):
        """Test validation of thousands grouping with decimal in US format."""
        # Test thousands grouping with decimal
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,234.56", candidate) is True
        assert validate("12,345.67", candidate) is True

    def test_should_validate_european_format(self):
        """Test validation of European number format."""
        # Test European format (dot thousands, comma decimal)
        candidate = LocaleCandidate(decimal=",", thousands=".", group_size=3, score=0)
        assert validate("1.234,56", candidate) is True
        assert validate("12.345,67", candidate) is True

    def test_should_validate_space_thousands_format(self):
        """Test validation of space as thousands separator."""
        # Test space as thousands separator
        candidate = LocaleCandidate(decimal=".", thousands=" ", group_size=3, score=0)
        assert validate("1 234.56", candidate) is True
        assert validate("12 345.67", candidate) is True

    def test_should_validate_apostrophe_thousands_format(self):
        """Test validation of apostrophe as thousands separator."""
        # Test apostrophe as thousands separator (Swiss format)
        candidate = LocaleCandidate(decimal=".", thousands="'", group_size=3, score=0)
        assert validate("1'234.56", candidate) is True
        assert validate("12'345.67", candidate) is True


class TestValidationDecimalSeparatorRules:
    """Test validation of decimal separator rules."""

    def test_should_reject_multiple_decimal_separators(self):
        """Test rejection of multiple decimal separators."""
        # Test rejection of multiple decimal separators
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.2.3", candidate) is False

    def test_should_reject_decimal_separator_mismatch(self):
        """Test rejection when wrong decimal separator is used."""
        # Test rejection when wrong decimal separator is used
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )
        assert validate("123,45", us_candidate) is False  # Comma not period

        eu_candidate = LocaleCandidate(
            decimal=",", thousands=".", group_size=3, score=0
        )
        assert validate("123.45", eu_candidate) is False  # Period not comma

    def test_should_validate_integer_without_decimal(self):
        """Test that integers without decimal separators are valid."""
        # Test that integers without decimal separators are valid
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("123", candidate) is True
        assert validate("1234", candidate) is True
        assert validate("12345", candidate) is True


class TestValidationThousandsGroupingRules:
    """Test validation of thousands grouping rules."""

    def test_should_reject_improper_thousands_grouping(self):
        """Test rejection of improper thousands grouping."""
        # Test rejection of improper thousands grouping
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,23,456", candidate) is False  # Second group too small
        assert validate("12,34", candidate) is False  # Second group too small

    def test_should_reject_consecutive_thousands_separators(self):
        """Test rejection of consecutive thousands separators."""
        # Test rejection of consecutive thousands separators
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,,234", candidate) is False
        assert validate("1,,,234", candidate) is False

    def test_should_reject_thousands_separator_at_start_or_end(self):
        """Test rejection of thousands separator at start or end."""
        # Test rejection of thousands separator at start or end
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate(",123", candidate) is False
        assert validate("123,", candidate) is False
        assert validate(",123,", candidate) is False

    def test_should_validate_leading_group_one_to_three_digits(self):
        """Test that leading group can have 1-3 digits."""
        # Test that leading group can have 1-3 digits
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,234", candidate) is True  # 1 digit
        assert validate("12,345", candidate) is True  # 2 digits
        assert validate("123,456", candidate) is True  # 3 digits

    def test_should_reject_thousands_separator_mismatch(self):
        """Test rejection when wrong thousands separator is used."""
        # Test rejection when wrong thousands separator is used
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )
        assert validate("1.234.567", us_candidate) is False  # Period not comma

        eu_candidate = LocaleCandidate(
            decimal=",", thousands=".", group_size=3, score=0
        )
        assert validate("1,234,567", eu_candidate) is False  # Comma not period


class TestScientificNotationRules:
    """Test validation of scientific notation rules."""

    def test_should_validate_basic_scientific_notation(self):
        """Test basic scientific notation validation."""
        # Test basic scientific notation validation
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e4", candidate) is True
        assert validate("1.23E4", candidate) is True
        assert validate("1.23e+4", candidate) is True
        assert validate("1.23E+4", candidate) is True

    def test_should_reject_thousands_in_scientific_mantissa(self):
        """Test rejection of thousands separators in scientific notation mantissa."""
        # Test rejection of thousands separators in scientific notation mantissa
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,234e4", candidate) is False
        assert validate("1,234e4", candidate) is False

    def test_should_validate_thousands_after_scientific_notation(self):
        """Test that thousands separators are not allowed in scientific notation."""
        # Test that thousands separators are allowed in exponent (if it's a valid
        # number). Actually, this is not realistic - exponents should be integers
        # without thousands separators
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e123", candidate) is True  # No thousands in exponent

    def test_should_reject_multiple_exponent_markers(self):
        """Test rejection of multiple e/E markers."""
        # Test rejection of multiple e/E markers
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e4e5", candidate) is False
        assert validate("1.23E4E5", candidate) is False

    def test_should_reject_decimal_in_exponent(self):
        """Test rejection of decimal separators in exponent."""
        # Test rejection of decimal separators in exponent
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e4.5", candidate) is False


class TestSignCharacters:
    """Test validation of sign characters."""

    def test_should_validate_negative_numbers(self):
        """Test validation of negative numbers."""
        # Test validation of negative numbers
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("-123", candidate) is True
        assert validate("-123.45", candidate) is True
        assert validate("-1,234.56", candidate) is True

    def test_should_validate_positive_numbers_with_sign(self):
        """Test validation of positive numbers with explicit sign."""
        # Test validation of positive numbers with explicit sign
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("+123", candidate) is True
        assert validate("+123.45", candidate) is True

    def test_should_validate_scientific_notation_with_signed_exponent(self):
        """Test scientific notation with signed exponents."""
        # Test scientific notation with signed exponents
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e+4", candidate) is True
        assert validate("1.23e-4", candidate) is True
        assert validate("-1.23e+4", candidate) is True
        assert validate("-1.23e-4", candidate) is True

    def test_should_reject_multiple_signs(self):
        """Test rejection of multiple sign characters."""
        # Test rejection of multiple sign characters
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("--123", candidate) is False
        assert validate("+-123", candidate) is False
        assert validate("++123", candidate) is False

    def test_should_reject_misplaced_signs(self):
        """Test rejection of misplaced sign characters."""
        # Test rejection of misplaced sign characters
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1-23", candidate) is False
        assert validate("123-", candidate) is False
        assert validate("12+34", candidate) is False
        assert validate("12+", candidate) is False


class TestEdgeCases:
    """Test validation of edge cases and special scenarios."""

    def test_should_reject_empty_string(self):
        """Test rejection of empty string."""
        # Test rejection of empty string
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("", candidate) is False

    def test_should_reject_only_separators(self):
        """Test rejection of strings with only separators."""
        # Test rejection of strings with only separators
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate(".", candidate) is False
        assert validate(",", candidate) is False
        assert validate(".,", candidate) is False

    def test_should_reject_invalid_characters(self):
        """Test rejection of invalid characters."""
        # Test rejection of invalid characters
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("123abc", candidate) is False
        assert validate("12@34.56", candidate) is False

    def test_should_validate_no_thousands_separator_candidate(self):
        """Test validation when candidate has no thousands separator."""
        # Test validation when candidate has no thousands separator
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)
        assert validate("123", candidate) is True
        assert validate("123.45", candidate) is True

    def test_should_reject_thousands_when_not_allowed(self):
        """Test rejection of thousands separators when candidate doesn't use them."""
        # Test rejection of thousands separators when candidate doesn't use them
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)
        assert validate("1,234.56", candidate) is False
        assert validate("1 234.56", candidate) is False

    def test_should_handle_unicode_space_thousands_separator(self):
        """Test validation with Unicode non-breaking space as thousands separator."""
        # Test validation with Unicode non-breaking space as thousands separator
        candidate = LocaleCandidate(
            decimal=",", thousands="\u00a0", group_size=3, score=0
        )
        assert validate("1\u00a0234,56", candidate) is True

    def test_should_reject_only_exponent_marker(self):
        """Test rejection of strings with only exponent markers."""
        # Test rejection of strings with only exponent markers
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("e", candidate) is False
        assert validate("E", candidate) is False


class TestComplexScenarios:
    """Test validation of complex real-world scenarios."""

    def test_should_validate_large_numbers_with_proper_grouping(self):
        """Test validation of large numbers with proper thousands grouping."""
        # Test validation of large numbers with proper thousands grouping
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1,234,567,890.12", candidate) is True
        assert validate("12,345,678.90", candidate) is True

    def test_should_validate_very_small_scientific_numbers(self):
        """Test validation of very small numbers in scientific notation."""
        # Test validation of very small numbers in scientific notation
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23E-10", candidate) is True
        assert validate("9.87E-123", candidate) is True

    def test_should_validate_zero_cases(self):
        """Test validation of zero in various formats."""
        # Test validation of zero in various formats
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("0", candidate) is True
        assert validate("0.0", candidate) is True
        assert validate("0.00", candidate) is True

    def test_should_validate_fractional_numbers_without_leading_zero(self):
        """Test validation of fractional numbers without leading zero."""
        # Test validation of fractional numbers without leading zero
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate(".123", candidate) is True
        assert validate(".5", candidate) is True

    def test_should_reject_decimal_after_thousands_violation(self):
        """Test complex case with both thousands and decimal violations."""
        # Test complex case with both thousands and decimal violations
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        # Both improper grouping and multiple decimals
        assert validate("1,23.45.67", candidate) is False


class TestCoverageTargets:
    """Additional tests to achieve 100% branch coverage."""

    def test_should_reject_empty_exponent(self):
        """Test rejection of empty exponent (scientific notation parsing edge case)."""
        # Test rejection of empty exponent (scientific notation parsing edge case)
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e", candidate) is False

    def test_should_reject_only_sign_in_exponent(self):
        """Test rejection of exponent with only sign."""
        # Test rejection of exponent with only sign
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e+", candidate) is False
        assert validate("1.23e-", candidate) is False

    def test_should_reject_only_sign_in_mantissa(self):
        """Test rejection of mantissa with only sign."""
        # Test rejection of mantissa with only sign
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("+", candidate) is False
        assert validate("-", candidate) is False

    def test_should_reject_fractional_part_with_thousands_separator(self):
        """Test rejection of thousands separator in fractional part."""
        # Test rejection of thousands separator in fractional part
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("123.45,67", candidate) is False

    def test_should_reject_empty_integer_part_in_split(self):
        """Test rejection when splitting thousands groups results in empty group."""
        # Test rejection when splitting thousands groups results in empty group
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        # Consecutive separators create empty groups
        assert validate("1,,234", candidate) is False

    def test_should_reject_non_digit_groups_in_thousands(self):
        """Test rejection of non-digit characters in thousands groups."""
        # Test rejection of non-digit characters in thousands groups
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        # This would be caught by character validation earlier, but covering the branch
        assert validate("1a3,456", candidate) is False

    def test_should_reject_leading_group_too_large(self):
        """Test rejection when leading group has more than group_size digits."""
        # Test rejection when leading group has more than group_size digits
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1234,567", candidate) is False  # Leading group has 4 digits

    def test_should_handle_candidate_without_decimal_separator(self):
        """Test validation when candidate has no thousands separator defined."""
        # Test validation when candidate has no thousands separator defined
        # (different case)
        candidate = LocaleCandidate(decimal=".", thousands=None, group_size=3, score=0)
        assert validate("1234", candidate) is True
        # This covers the None thousands separator branch

    def test_should_reject_decimal_at_end(self):
        """Test rejection of decimal separator at the end."""
        # Test rejection of decimal separator at the end
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("123.", candidate) is False

    def test_should_handle_exponent_without_sign(self):
        """Test scientific notation exponent without explicit sign."""
        # Test scientific notation exponent without explicit sign
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e123", candidate) is True


class TestSpecificBranches:
    """Very specific tests targeting exact uncovered branches."""

    def test_should_handle_empty_mantissa_case(self):
        """Test edge case where mantissa becomes empty after processing."""
        # Test edge case where mantissa becomes empty after processing
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        # This is actually just testing empty string validation
        assert validate("", candidate) is False

    def test_should_handle_signed_numbers_with_multiple_signs_in_different_positions(
        self,
    ):
        """Test various positions for multiple signs to hit different branches."""
        # Test various positions for multiple signs to hit different branches
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("++123", candidate) is False  # Multiple signs at start
        assert validate("+-123", candidate) is False  # Different signs at start
        assert validate("12+", candidate) is False  # Sign at end

    def test_should_handle_exponent_with_empty_or_invalid_cases(self):
        """Test exponent validation edge cases."""
        # Test exponent validation edge cases
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        assert validate("1.23e", candidate) is False
        assert validate("1.23e+", candidate) is False
        assert validate("1.23ea", candidate) is False

    def test_should_handle_thousands_separator_edge_cases(self):
        """Test edge cases in thousands separator validation."""
        # Test edge cases in thousands separator validation
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        # Empty groups from consecutive separators
        assert validate("1,,234", candidate) is False
        # Single digit group (valid for leading)
        assert validate("1,234", candidate) is True
        # Four digit leading group (invalid)
        assert validate("1234,567", candidate) is False

    def test_should_validate_no_scientific_notation_path(self):
        """Test the path where no scientific notation is detected."""
        # Test the path where no scientific notation is detected
        candidate = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        # Regular numbers without e/E
        assert validate("123.45", candidate) is True
        # Number with e/E at start or end (not scientific notation)
        assert validate("e123", candidate) is False
        assert validate("123e", candidate) is False


class TestMissingValidationCoverage:
    """Additional tests to achieve 100% coverage for missing validation branches."""

    def test_should_cover_validate_exponent_edge_cases(self):
        """Test _validate_exponent edge cases."""
        # Test empty exponent
        assert not _validate_exponent("")

        # Test exponent with only sign (no digits)
        assert not _validate_exponent("+")
        assert not _validate_exponent("-")

        # Test valid exponents
        assert _validate_exponent("123")
        assert _validate_exponent("+123")
        assert _validate_exponent("-123")

    def test_should_cover_validate_characters_and_signs_edge_cases(self):
        """Test _validate_characters_and_signs edge cases."""
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )

        # Test with only sign (no digits)
        valid, idx = _validate_characters_and_signs("+", us_candidate)
        assert not valid
        assert idx == 0

        # Test with multiple signs
        valid, idx = _validate_characters_and_signs("+-123", us_candidate)
        assert not valid
        assert idx == 0

        # Test with invalid characters
        valid, idx = _validate_characters_and_signs("12@34", us_candidate)
        assert not valid
        assert idx == 0

    def test_should_cover_validate_decimal_parts_edge_cases(self):
        """Test _validate_decimal_parts edge cases."""
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )

        # Test with empty fractional part
        valid, integer_part = _validate_decimal_parts("123.", us_candidate)
        assert not valid
        assert integer_part == ""

        # Test with non-digit fractional part
        valid, integer_part = _validate_decimal_parts("123.abc", us_candidate)
        assert not valid
        assert integer_part == ""

        # Test with multiple decimal separators
        valid, integer_part = _validate_decimal_parts("123.45.67", us_candidate)
        assert not valid
        assert integer_part == ""

        # Test with empty integer part (valid fractional number)
        valid, integer_part = _validate_decimal_parts(".123", us_candidate)
        assert valid
        assert integer_part == ""

    def test_should_cover_validate_integer_part_edge_cases(self):
        """Test _validate_integer_part edge cases."""
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )

        # Test with empty integer part
        assert not _validate_integer_part("", us_candidate)

        # Test with candidate that has no thousands separator
        no_thousands_candidate = LocaleCandidate(
            decimal=".", thousands=None, group_size=3, score=0
        )
        assert _validate_integer_part("123", no_thousands_candidate)
        assert not _validate_integer_part("12a3", no_thousands_candidate)

        # Test with single group that is empty
        assert not _validate_integer_part("", us_candidate)

        # Test with single group that has invalid characters
        assert not _validate_integer_part("12a3", us_candidate)

    def test_should_cover_validate_thousands_groups_edge_cases(self):
        """Test _validate_thousands_groups edge cases."""
        us_candidate = LocaleCandidate(
            decimal=".", thousands=",", group_size=3, score=0
        )

        # Test with empty group
        assert not _validate_thousands_groups(["123", "", "456"], us_candidate)

        # Test with non-digit group
        assert not _validate_thousands_groups(["123", "abc", "456"], us_candidate)

        # Test with leading group too large
        assert not _validate_thousands_groups(["1234", "567", "890"], us_candidate)

        # Test with subsequent group wrong size
        assert not _validate_thousands_groups(["123", "45", "890"], us_candidate)

        # Test with valid groups
        assert _validate_thousands_groups(["1", "234", "567"], us_candidate)
        assert _validate_thousands_groups(["12", "234", "567"], us_candidate)
        assert _validate_thousands_groups(["123", "234", "567"], us_candidate)
