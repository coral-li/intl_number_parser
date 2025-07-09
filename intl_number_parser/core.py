"""Core number parsing engine for international number formats.

This module provides the main parse_number function that converts tokens
from any international number format to canonical Python numeric values.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .detector import LocaleDetector
from .unicode import normalize_token
from .validation import validate

if TYPE_CHECKING:
    from .candidates import LocaleCandidate

# Maximum value for 64-bit signed integer
MAX_INT64 = 2**63 - 1

# Error message constant
_NO_VALID_NUMBER_MSG = "No valid number found in token"

# Constants for magic numbers
_SCIENTIFIC_NOTATION_PARTS = 2
_THOUSANDS_GROUP_SIZE = 3


def parse_number(token: str, detector: LocaleDetector | None = None) -> str | int:
    """Parse an international number format into canonical Python numeric value.

    This function converts numeric tokens from any international format into
    canonical Python numeric representation. It handles locale detection,
    precision constraints, and embedded number extraction.

    Args:
        token: The input token containing a number (may be embedded in text)
        detector: Optional LocaleDetector for format detection. If None,
                 creates a temporary detector for per-token autodetection.

    Returns:
        int: For integers within 2^63-1 range
        str: For decimals, scientific notation, or integers > 2^63-1
             (suitable for decimal.Decimal or float conversion)

    Raises:
        ValueError: If no valid number is found in the token

    Examples:
        >>> parse_number("1,234.56")
        '1234.56'
        >>> parse_number("42")
        42
        >>> parse_number("1.23e4")
        '1.23e4'
        >>> parse_number("Price: €1.234,56")
        '1234.56'
    """
    if not token:
        raise ValueError(_NO_VALID_NUMBER_MSG)

    # Normalize the input token
    normalized_token = normalize_token(token)

    if not normalized_token:
        raise ValueError(_NO_VALID_NUMBER_MSG)

    # Extract the first valid number from the normalized token
    extraction_result = _extract_number_from_text(normalized_token, detector)

    if extraction_result is None:
        raise ValueError(_NO_VALID_NUMBER_MSG)

    extracted_number, used_candidate = extraction_result

    # Validate token for invalid patterns (multiple decimal points, etc.)
    if not _is_valid_number_format(normalized_token):
        raise ValueError(_NO_VALID_NUMBER_MSG)

    # Parse the extracted number to canonical form using candidate info
    canonical_number = _parse_to_canonical(extracted_number, used_candidate)

    # Apply precision constraints
    return _apply_precision_constraints(canonical_number)


def _is_valid_number_format(text: str) -> bool:
    """Validate that text doesn't contain obvious invalid number patterns.

    Args:
        text: The text to validate for invalid number patterns

    Returns:
        True if valid, False if contains invalid patterns
        (e.g., multiple decimal points)
    """
    # Check for obvious invalid patterns:
    # 1. Consecutive separators like ".." or ",,"
    # 2. Multiple decimal points that are clearly not thousands separators

    # Patterns for clearly invalid formats (consecutive separators)
    invalid_patterns = [
        r"\.\.",  # .. (consecutive periods)
        r",,",  # ,, (consecutive commas)
        r"\.,",  # ., (mixed consecutive)
        r",\.",  # ,. (mixed consecutive)
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, text):
            return False

    # Check for multiple decimal indicators in same number
    # This is more complex as we need to distinguish thousands from decimals

    # Look for patterns that suggest multiple decimal points in the same number
    # A decimal point is likely if it's followed by 1-2 digits (not 3)
    # Thousands separators are typically followed by exactly 3 digits

    # Pattern for potential multiple decimals: X.Y.Z where Y and Z
    # are not exactly 3 digits
    decimal_like_pattern = r"\d+\.(?:\d{1,2}|\d{4,})\.\d+"
    if re.search(decimal_like_pattern, text):
        # Additional check: ensure this isn't a valid thousands pattern
        # Valid: 1.234.567 (periods separate groups of 3)
        # Invalid: 1.23.45 or 1.2345.67
        thousands_pattern = r"\d{1,3}(?:\.\d{3})+(?:[,\.]\d+)?$"
        if not re.match(thousands_pattern, text.strip()):
            return False

    # Similar check for comma patterns
    comma_decimal_pattern = r"\d+,(?:\d{1,2}|\d{4,}),\d+"
    if re.search(comma_decimal_pattern, text):
        # Check if it's a valid thousands pattern with commas
        comma_thousands_pattern = r"\d{1,3}(?:,\d{3})+(?:[,\.]\d+)?$"
        if not re.match(comma_thousands_pattern, text.strip()):
            return False

    return True


def _extract_number_from_text(
    text: str, detector: LocaleDetector | None
) -> tuple[str, LocaleCandidate | None] | None:
    """Extract the first valid number from text using locale detection.

    Args:
        text: Normalized text that may contain embedded numbers
        detector: LocaleDetector for format detection

    Returns:
        The first valid number string found, or None if no valid number
    """
    # Get the best candidate from detector or create temporary one
    if detector is not None:
        best_candidate = detector.best_candidate
    else:
        # Create temporary detector for per-token autodetection
        temp_detector = LocaleDetector()
        temp_detector.ingest(text)
        best_candidate = temp_detector.best_candidate

    # Try to extract number using the best candidate
    if best_candidate is not None:
        number = _extract_with_candidate(text, best_candidate)
        if number is not None:
            return (number, best_candidate)

    # Fallback: try all common patterns if candidate-based extraction fails
    fallback_number = _extract_with_fallback_patterns(text)
    if fallback_number is not None:
        # For fallback, we don't have a specific candidate, return None
        return (fallback_number, None)

    return None


def _extract_with_candidate(text: str, candidate: LocaleCandidate) -> str | None:
    """Extract number using a specific locale candidate.

    Args:
        text: Text to search for numbers
        candidate: LocaleCandidate defining the format

    Returns:
        First valid number string or None
    """
    # Build regex pattern for this candidate
    pattern = _build_number_pattern(candidate)

    # Find all potential matches
    matches = re.finditer(pattern, text)

    for match in matches:
        number_str = match.group(0)
        # Validate the match against the candidate
        if validate(number_str, candidate):
            return number_str

    return None


def _extract_with_fallback_patterns(text: str) -> str | None:
    """Extract number using fallback patterns when candidate detection fails.

    Args:
        text: Text to search for numbers

    Returns:
        First valid number string or None
    """
    # Simple patterns for basic number formats (most permissive)
    fallback_patterns = [
        # Scientific notation (highest priority)
        r"[+-]?(?:\d+(?:[,\s\'\u00a0]\d{3})*\.?\d*|\.\d+)[eE][+-]?\d+",
        # Decimal numbers with thousands separators - US format: 1,234.56
        r"[+-]?\d{1,3}(?:,[0-9]{3})*\.[0-9]+",
        # Decimal numbers with thousands separators - EU format: 1.234,56
        r"[+-]?\d{1,3}(?:\.[0-9]{3})*,[0-9]+",
        # Decimal numbers with space thousands separators: 1 234.56 or 1 234,56
        r"[+-]?\d{1,3}(?:[\s\u00a0][0-9]{3})*[.,][0-9]+",
        # Decimal numbers with apostrophe thousands: 1'234.56
        r"[+-]?\d{1,3}(?:\'[0-9]{3})*\.[0-9]+",
        # Simple decimal numbers (including trailing decimal: 123.)
        r"[+-]?(?:\d+\.\d*|\.\d+)",
        # Integer with comma thousands: 1,234,567 (no decimal)
        r"[+-]?\d{1,3}(?:,[0-9]{3})+(?![.,0-9])",
        # Integer with period thousands: 1.234.567 (no decimal)
        r"[+-]?\d{1,3}(?:\.[0-9]{3})+(?![.,0-9])",
        # Integer with space thousands: 1 234 567 (no decimal)
        r"[+-]?\d{1,3}(?:[\s\u00a0][0-9]{3})+(?![.,0-9])",
        # Integer with apostrophe thousands: 1'234'567 (no decimal)
        r"[+-]?\d{1,3}(?:\'[0-9]{3})+(?![.,0-9])",
        # Simple integer
        r"[+-]?\d+",
    ]

    for pattern in fallback_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            # Return first match found
            return match.group(0)

    return None


def _build_number_pattern(candidate: LocaleCandidate) -> str:
    """Build regex pattern for extracting numbers in a specific locale format.

    Args:
        candidate: LocaleCandidate defining the format

    Returns:
        Regex pattern string
    """
    # Escape special regex characters
    decimal_char = re.escape(candidate.decimal)
    thousands_char = re.escape(candidate.thousands) if candidate.thousands else None

    # Build pattern components
    sign_part = r"[+-]?"

    if thousands_char:
        # Pattern that allows both with and without thousands separators
        # Format with thousands: 1,234,567 or 1,234.56
        group_size = candidate.group_size
        with_thousands = rf"\d{{1,{group_size}}}(?:{thousands_char}\d{{{group_size}}})+"
        # Format without thousands: 1234567 or 1234.56
        without_thousands = r"\d+"
        # Integer part can be either
        integer_part = rf"(?:{with_thousands}|{without_thousands})"
    else:
        # Pattern without thousands separators
        integer_part = r"\d+"

    # Decimal part is optional
    decimal_part = rf"(?:{decimal_char}\d+)?"

    # Scientific notation part is optional
    scientific_part = r"(?:[eE][+-]?\d+)?"

    # Build complete pattern
    # Allow: integer[.decimal][e/E±exponent] OR .decimal[e/E±exponent]
    return (
        rf"{sign_part}(?:{integer_part}{decimal_part}|"
        rf"{decimal_char}\d+){scientific_part}"
    )


def _parse_to_canonical(
    number_str: str, candidate: LocaleCandidate | None = None
) -> str:
    """Parse a number string to canonical form.

    Args:
        number_str: Number string in some international format
        candidate: Optional locale candidate to use for parsing

    Returns:
        Canonical number string (suitable for float() or int())
    """
    canonical = number_str.strip()

    # Handle scientific notation first (preserve it exactly)
    if "e" in canonical.lower():
        # Split on e/E
        parts = re.split(pattern=r"[eE]", string=canonical, maxsplit=1)
        if len(parts) == _SCIENTIFIC_NOTATION_PARTS:
            mantissa_part = parts[0]
            exponent_part = parts[1]

            # Parse mantissa part only
            canonical_mantissa = _parse_mantissa_to_canonical(mantissa_part, candidate)

            # Reconstruct with original case e/E
            e_char = "e" if "e" in canonical else "E"
            return canonical_mantissa + e_char + exponent_part

    # Not scientific notation - parse as regular number
    return _parse_mantissa_to_canonical(canonical, candidate)


def _is_potential_decimal_separator(canonical: str, pos: int, after_text: str) -> bool:
    """Check if a separator at given position could be a decimal separator."""
    # Check basic pattern: followed by 1-3 digits or nothing (trailing decimal)
    if not (re.match(r"^\d{1,3}(?![0-9])", after_text) or after_text == ""):
        return False

    # Not followed by exactly 3 digits then another separator
    if re.match(r"^\d{3}[,.\s\'\u00a0]", after_text):
        return False

    return not _is_thousands_pattern(canonical, pos, after_text)


def _is_thousands_pattern(canonical: str, pos: int, after_text: str) -> bool:
    """Check if separator is part of a thousands grouping pattern."""
    # Trailing decimal points are never thousands
    if after_text == "":
        return False

    # Only check for thousands pattern if exactly 3 digits at end
    if len(after_text) != _THOUSANDS_GROUP_SIZE:
        return False

    # Check if there's a pattern of separators before this
    before_text = canonical[:pos]
    thousands_groups = re.findall(r"[,.\s\'\u00a0]\d{3}", before_text)
    return bool(thousands_groups)


def _normalize_canonical_number(canonical: str) -> str:
    """Normalize canonical number by handling edge cases."""
    # Handle leading decimal point cases
    if canonical.startswith("."):
        canonical = "0" + canonical
    elif canonical.startswith("+."):
        canonical = "0" + canonical[1:]
    elif canonical.startswith("-."):
        canonical = "-0" + canonical[1:]

    # Handle trailing decimal point case
    if canonical.endswith("."):
        canonical += "0"

    # Normalize positive sign (remove leading +)
    if canonical.startswith("+"):
        canonical = canonical[1:]

    return canonical


def _parse_mantissa_to_canonical(
    mantissa_str: str, candidate: LocaleCandidate | None = None
) -> str:
    """Parse mantissa part (non-scientific notation) to canonical form."""
    canonical = mantissa_str.strip()

    if candidate is not None:
        # Use candidate information to properly interpret separators
        decimal_char = candidate.decimal
        thousands_char = candidate.thousands

        # Find the rightmost decimal separator if any
        decimal_pos = canonical.rfind(decimal_char) if decimal_char in canonical else -1

        if decimal_pos >= 0:
            # Split at decimal position
            before_decimal = canonical[:decimal_pos]
            after_decimal = canonical[decimal_pos + 1 :]

            # Remove thousands separators from integer part
            if thousands_char:
                before_decimal = before_decimal.replace(thousands_char, "")

            # Keep only digits in decimal part (up to first non-digit)
            decimal_match = re.match(r"(\d+)", after_decimal)
            decimal_digits = decimal_match.group(1) if decimal_match else ""

            canonical = before_decimal + "." + decimal_digits
        # No decimal separator - just remove thousands separators
        elif thousands_char:
            canonical = canonical.replace(thousands_char, "")
    else:
        # Fallback: use original auto-detection logic when no candidate
        # Find all potential decimal separators
        potential_decimals = []
        for match in re.finditer(r"[.,]", canonical):
            pos = match.start()
            char = match.group()
            after_text = canonical[pos + 1 :]

            if _is_potential_decimal_separator(canonical, pos, after_text):
                potential_decimals.append((pos, char))

        # Use the rightmost potential decimal separator
        if potential_decimals:
            decimal_pos, decimal_char = potential_decimals[-1]

            # Split at decimal position
            before_decimal = canonical[:decimal_pos]
            after_decimal = canonical[decimal_pos + 1 :]

            # Remove all thousands separators from before decimal
            before_decimal = re.sub(r"[,.\s\'\u00a0]", "", before_decimal)

            # Keep only digits in decimal part (up to first non-digit)
            decimal_match = re.match(r"(\d+)", after_decimal)
            decimal_digits = decimal_match.group(1) if decimal_match else ""

            canonical = before_decimal + "." + decimal_digits
        else:
            # No decimal separator found - remove all thousands separators
            canonical = re.sub(r"[,.\s\'\u00a0]", "", canonical)

    return _normalize_canonical_number(canonical)


def _apply_precision_constraints(canonical_number: str) -> str | int:
    """Apply precision constraints to determine return type.

    Args:
        canonical_number: Number in canonical string form

    Returns:
        int for integers ≤ 2^63-1, str otherwise
    """
    # Check if it's a decimal number or scientific notation
    if "." in canonical_number or "e" in canonical_number.lower():
        return canonical_number

    # It's an integer - check if it fits in 64-bit signed range
    try:
        int_value = int(canonical_number)
        if -MAX_INT64 - 1 <= int_value <= MAX_INT64:
            return int_value
        return canonical_number  # noqa: TRY300
    except ValueError:
        # Shouldn't happen with well-formed canonical numbers,
        # but return string as fallback
        return canonical_number
