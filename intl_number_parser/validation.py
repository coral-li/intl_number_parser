"""Validation logic for numeric tokens against locale candidates.

This module provides structural validation of numeric tokens to determine
if they conform to a given LocaleCandidate's formatting rules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .candidates import LocaleCandidate

# Constants for decimal part validation
MAX_DECIMAL_PARTS = 2


def validate(token: str, candidate: LocaleCandidate) -> bool:
    """Validate a numeric token against a LocaleCandidate's formatting rules.

    Validates that the token conforms to the candidate's decimal and thousands
    separator rules, proper grouping, and scientific notation constraints.

    Validation rules:
    1. Exactly one decimal separator permitted (or none for integers)
    2. Thousands groups must be exactly `group_size` digits each, except
       the leading group which may have 1-group_size digits
    3. No thousands separators allowed inside mantissa when scientific notation present
    4. Only valid characters allowed: digits, decimal separator, thousands separator,
       exponent markers (e/E), sign characters (+/-)

    Args:
        token: The normalized token to validate
        candidate: The LocaleCandidate to validate against

    Returns:
        True if token conforms to candidate's rules, False otherwise

    Examples:
        >>> from intl_number_parser.candidates import LocaleCandidate
        >>> us_format = LocaleCandidate(
        ...     decimal=".", thousands=",", group_size=3, score=0
        ... )
        >>> validate("1,234.56", us_format)
        True
        >>> validate("1,23.56", us_format)  # Invalid grouping
        False
    """
    if not token:
        return False

    # Check for scientific notation first to split mantissa and exponent
    mantissa, exponent = _split_scientific_notation(token)

    # Validate exponent part if present
    if exponent is not None:
        if not _validate_exponent(exponent):
            return False
        # No thousands separators allowed in mantissa when scientific notation present
        if candidate.thousands and candidate.thousands in mantissa:
            return False

    # Validate the mantissa (or entire token if no scientific notation)
    return _validate_mantissa(mantissa, candidate)


def _split_scientific_notation(token: str) -> tuple[str, str | None]:
    """Split token into mantissa and exponent parts if scientific notation present.

    Returns:
        Tuple of (mantissa, exponent) where exponent is None if no scientific notation
    """
    # Find e or E that's not at start or end
    e_index = -1
    for i, char in enumerate(token):
        if char in "eE" and 0 < i < len(token) - 1:
            e_index = i
            break

    if e_index == -1:
        return token, None

    # Check for multiple e/E markers
    remaining = token[e_index + 1 :]
    if "e" in remaining or "E" in remaining:
        return token, None  # Invalid - will be caught by validation

    mantissa = token[:e_index]
    exponent = token[e_index + 1 :]

    return mantissa, exponent


def _validate_exponent(exponent: str) -> bool:
    """Validate the exponent part of scientific notation.

    Exponent must be a valid integer (optionally signed).
    """
    if not exponent:
        return False

    # Handle optional sign
    start_idx = 0
    if exponent[0] in "+-":
        start_idx = 1
        if len(exponent) == 1:  # Only sign, no digits
            return False

    # Rest must be digits
    return exponent[start_idx:].isdigit()


def _validate_characters_and_signs(
    mantissa: str, candidate: LocaleCandidate
) -> tuple[bool, int]:
    """Validate characters and sign placement in mantissa.

    Returns:
        Tuple of (is_valid, start_index_after_sign)
    """
    # Check for invalid characters first
    valid_chars = set("0123456789+-")
    if candidate.decimal:
        valid_chars.add(candidate.decimal)
    if candidate.thousands:
        valid_chars.add(candidate.thousands)

    if not all(char in valid_chars for char in mantissa):
        return False, 0

    # Handle sign at the beginning
    start_idx = 0
    if mantissa[0] in "+-":
        start_idx = 1
        if len(mantissa) == 1:  # Only sign, no digits
            return False, 0
        # Check for multiple signs or signs in middle/end
        if any(c in "+-" for c in mantissa[1:]):
            return False, 0

    return True, start_idx


def _validate_decimal_parts(
    working_part: str, candidate: LocaleCandidate
) -> tuple[bool, str]:
    """Validate decimal separator usage and return integer part.

    Returns:
        Tuple of (is_valid, integer_part)
    """
    # Split by decimal separator if present
    decimal_parts = (
        working_part.split(candidate.decimal) if candidate.decimal else [working_part]
    )

    # Check decimal separator rules
    if len(decimal_parts) > MAX_DECIMAL_PARTS:
        return False, ""  # Multiple decimal separators

    if len(decimal_parts) == MAX_DECIMAL_PARTS:
        # Has decimal separator
        integer_part, fractional_part = decimal_parts

        # Fractional part must contain only digits (no thousands separators)
        if not fractional_part or not fractional_part.isdigit():
            return False, ""

        # For numbers like ".123", integer part can be empty
        if not integer_part:
            return True, ""  # Valid fractional number without leading zero

        return True, integer_part

    # No decimal separator
    return True, decimal_parts[0]


def _validate_mantissa(mantissa: str, candidate: LocaleCandidate) -> bool:
    """Validate the mantissa part against locale candidate rules."""
    if not mantissa:
        return False

    # Validate characters and signs
    chars_valid, start_idx = _validate_characters_and_signs(mantissa, candidate)
    if not chars_valid:
        return False

    working_part = mantissa[start_idx:]

    # Validate decimal parts
    decimal_valid, integer_part = _validate_decimal_parts(working_part, candidate)
    if not decimal_valid:
        return False

    # If we have a valid fractional number without integer part, we're done
    if not integer_part:
        return True

    # Validate integer part
    return _validate_integer_part(integer_part, candidate)


def _validate_thousands_groups(groups: list[str], candidate: LocaleCandidate) -> bool:
    """Validate thousands separator grouping rules."""
    for i, group in enumerate(groups):
        if not group or not group.isdigit():
            return False

        if i == 0:
            # Leading group can have 1 to group_size digits
            if not (1 <= len(group) <= candidate.group_size):
                return False
        # All other groups must have exactly group_size digits
        elif len(group) != candidate.group_size:
            return False

    return True


def _validate_integer_part(integer_part: str, candidate: LocaleCandidate) -> bool:
    """Validate the integer part of a number."""
    if not integer_part:
        return False

    # If no thousands separator defined, entire part must be digits
    if not candidate.thousands:
        return integer_part.isdigit()

    # Split by thousands separator
    groups = integer_part.split(candidate.thousands)

    # If only one group, it must be digits and non-empty
    if len(groups) == 1:
        return groups[0].isdigit() and groups[0] != ""

    # Multiple groups - validate thousands grouping rules
    return _validate_thousands_groups(groups, candidate)
