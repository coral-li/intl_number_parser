"""Core number parsing engine for international number formats.

This module provides the main parse_number function that converts tokens
from any international number format to canonical Python numeric values.
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING

from .detector import LocaleDetector
from .unicode import _normalize_token_for_parsing, normalize_token
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
_REPEATED_SEPARATOR_COUNT = 2
_ACCOUNTING_FRACTIONAL_DIGITS = 2
_ACCOUNTING_PARENTHESES_PATTERN = re.compile(r"\(([^()]*)\)")
_CURRENCY_SYMBOL_CATEGORY = "Sc"


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
    normalized_token = _normalize_token_for_parsing(
        _apply_accounting_negative_notation(token)
    )

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


def _apply_accounting_negative_notation(token: str) -> str:
    """Convert clear accounting-negative parenthesized spans to signed spans."""
    normalized = unicodedata.normalize("NFKC", token)
    if "(" not in normalized or ")" not in normalized:
        return normalized

    result: list[str] = []
    last_end = 0
    for match in _ACCOUNTING_PARENTHESES_PATTERN.finditer(normalized):
        result.append(normalized[last_end : match.start()])
        inner = match.group(1)
        if _is_accounting_negative_span(normalized, match.start(), match.end(), inner):
            result.append(f"-{inner.strip()}")
        else:
            result.append(match.group(0))
        last_end = match.end()

    result.append(normalized[last_end:])
    return "".join(result)


def _is_accounting_negative_span(text: str, start: int, end: int, inner: str) -> bool:
    """Return True when a parenthesized span clearly represents a negative number."""
    stripped_inner = inner.strip()
    if not stripped_inner:
        return False

    normalized_inner = normalize_token(stripped_inner).strip()
    if not normalized_inner or not any(char.isdigit() for char in normalized_inner):
        return False

    if normalized_inner[0] in "+-":
        return False

    if _span_covers_entire_token(text, start, end):
        return True

    return _contains_currency_symbol(stripped_inner) or _has_accounting_number_shape(
        normalized_inner
    )


def _span_covers_entire_token(text: str, start: int, end: int) -> bool:
    """Return True when the parenthesized span is the whole token."""
    return not text[:start].strip() and not text[end:].strip()


def _contains_currency_symbol(text: str) -> bool:
    """Return True when text contains a Unicode currency symbol."""
    return any(unicodedata.category(char) == _CURRENCY_SYMBOL_CATEGORY for char in text)


def _has_accounting_number_shape(normalized_text: str) -> bool:
    """Return True for embedded amount-like accounting numbers."""
    return _has_accounting_thousands_group(
        normalized_text
    ) or _has_accounting_decimal_amount(normalized_text)


def _has_accounting_thousands_group(normalized_text: str) -> bool:
    """Return True when text has a valid thousands-grouped number shape."""
    for separator in (",", ".", " ", "'"):
        if separator in normalized_text and _is_valid_thousands_pattern_text(
            normalized_text, separator
        ):
            return True
    return False


def _has_accounting_decimal_amount(normalized_text: str) -> bool:
    """Return True for decimal amounts with two fractional digits."""
    for separator in (".", ","):
        separator_position = normalized_text.rfind(separator)
        if separator_position == -1:
            continue

        fractional_part = normalized_text[separator_position + 1 :]
        integer_part = normalized_text[:separator_position]
        if (
            len(fractional_part) == _ACCOUNTING_FRACTIONAL_DIGITS
            and fractional_part.isdigit()
            and any(char.isdigit() for char in integer_part)
        ):
            return True

    return False


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

    period_count = 0
    comma_count = 0
    previous_char = ""
    for char in text:
        if char == ".":
            period_count += 1
            if previous_char in (".", ","):
                return False
        elif char == ",":
            comma_count += 1
            if previous_char in (".", ","):
                return False
        previous_char = char

    if (
        period_count < _REPEATED_SEPARATOR_COUNT
        and comma_count < _REPEATED_SEPARATOR_COUNT
    ):
        return True

    # Check for multiple decimal indicators in same number
    # This is more complex as we need to distinguish thousands from decimals

    # Look for patterns that suggest multiple decimal points in the same number
    # A decimal point is likely if it's followed by 1-2 digits (not 3)
    # Thousands separators are typically followed by exactly 3 digits

    return not (
        _has_invalid_repeated_separator_group(text, ".", period_count)
        or _has_invalid_repeated_separator_group(text, ",", comma_count)
    )


def _has_invalid_repeated_separator_group(
    text: str, separator: str, separator_count: int
) -> bool:
    """Return True when repeated separators cannot be valid thousands groups."""
    if separator_count < _REPEATED_SEPARATOR_COUNT:
        return False

    separator_positions = [
        index for index, char in enumerate(text) if char == separator
    ]
    for left_pos, right_pos in zip(separator_positions, separator_positions[1:]):
        if left_pos == 0 or right_pos >= len(text) - 1:
            continue

        middle_group = text[left_pos + 1 : right_pos]
        if not middle_group or not middle_group.isdigit():
            continue

        if not (text[left_pos - 1].isdigit() and text[right_pos + 1].isdigit()):
            continue

        if len(middle_group) != _THOUSANDS_GROUP_SIZE:
            return not _is_valid_thousands_pattern_text(text.strip(), separator)

    return False


def _is_valid_thousands_pattern_text(text: str, separator: str) -> bool:
    """Check the historical thousands pattern shape without regex backtracking."""
    position = 0
    text_length = len(text)

    first_group_start = position
    while position < text_length and text[position].isdigit():
        position += 1

    first_group_size = position - first_group_start
    if not 1 <= first_group_size <= _THOUSANDS_GROUP_SIZE:
        return False

    thousands_groups = 0
    while position < text_length and text[position] == separator:
        group_start = position + 1
        group_end = group_start
        while group_end < text_length and text[group_end].isdigit():
            group_end += 1

        if group_end - group_start != _THOUSANDS_GROUP_SIZE:
            break

        thousands_groups += 1
        position = group_end

    if thousands_groups == 0:
        return False

    if position == text_length:
        return True

    if text[position] not in ",.":
        return False

    position += 1
    decimal_start = position
    while position < text_length and text[position].isdigit():
        position += 1

    return position > decimal_start and position == text_length


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
        return (fallback_number, _infer_fallback_candidate(fallback_number))

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
    best_match: tuple[int, str] | None = None
    for scientific_match in _iter_scientific_notation_matches(text):
        best_match = _earlier_fallback_match(best_match, scientific_match)

    # Simple patterns for basic number formats (most permissive)
    fallback_patterns = [
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
        for regex_match in matches:
            best_match = _earlier_fallback_match(
                best_match, (regex_match.start(), regex_match.group(0))
            )

    return best_match[1] if best_match is not None else None


def _earlier_fallback_match(
    current: tuple[int, str] | None, candidate: tuple[int, str]
) -> tuple[int, str]:
    """Return the earlier match, preferring longer same-start matches."""
    if current is None or candidate[0] < current[0]:
        return candidate
    if candidate[0] == current[0] and len(candidate[1]) > len(current[1]):
        return candidate
    return current


def _infer_fallback_candidate(number_str: str) -> LocaleCandidate | None:
    """Infer parse context for a fallback-extracted number."""
    detector = LocaleDetector()
    detector.ingest(number_str)
    return detector.best_candidate


def _iter_scientific_notation_matches(text: str) -> list[tuple[int, str]]:
    """Extract scientific notation matches without a backtracking regex."""
    matches: list[tuple[int, str]] = []
    text_length = len(text)
    index = 0

    while index < text_length:
        scientific_number, next_index = _scan_scientific_candidate(text, index)
        if scientific_number is not None:
            matches.append((index, scientific_number))
        index = next_index

    return matches


def _extract_scientific_notation_linear(text: str) -> str | None:
    """Extract basic scientific notation without a backtracking regex."""
    matches = _iter_scientific_notation_matches(text)
    return matches[0][1] if matches else None


def _scan_scientific_candidate(text: str, start: int) -> tuple[str | None, int]:
    """Scan one possible scientific notation candidate from start."""
    next_index = start + 1

    index = _consume_scientific_prefix(text, start)
    if index is None:
        return None, next_index

    index, digits_seen = _consume_scientific_mantissa(text, index)

    if digits_seen == 0:
        return None, next_index

    if index >= len(text) or text[index] not in "eE":
        return None, max(index, next_index)

    exponent_index = _consume_scientific_exponent(text, index)
    if exponent_index is None:
        return None, index + 1

    return text[start:exponent_index], exponent_index


def _consume_scientific_prefix(text: str, start: int) -> int | None:
    """Return the mantissa start after an optional sign, or None."""
    if text[start] in "+-":
        next_index = start + 1
        if next_index >= len(text):
            return None
        if text[next_index].isdigit() or text[next_index] == ".":
            return next_index
        return None

    if text[start].isdigit() or text[start] == ".":
        return start

    return None


def _consume_scientific_mantissa(text: str, start: int) -> tuple[int, int]:
    """Consume a basic period-decimal mantissa and count its digits."""
    text_length = len(text)
    index = start
    digits_seen = 0

    if text[index] == ".":
        index += 1
        while index < text_length and text[index].isdigit():
            index += 1
            digits_seen += 1
        return index, digits_seen

    while index < text_length and text[index].isdigit():
        index += 1
        digits_seen += 1

    while _has_scientific_group(text, index):
        index += 1
        group_end = index + _THOUSANDS_GROUP_SIZE
        digits_seen += _THOUSANDS_GROUP_SIZE
        index = group_end

    if index < text_length and text[index] == ".":
        index += 1
        while index < text_length and text[index].isdigit():
            index += 1
            digits_seen += 1
    else:
        while index < text_length and text[index].isdigit():
            index += 1
            digits_seen += 1

    return index, digits_seen


def _has_scientific_group(text: str, index: int) -> bool:
    """Return True when index starts an old-regex-compatible thousands group."""
    if index >= len(text) or not _is_scientific_group_separator(text[index]):
        return False

    group_start = index + 1
    group_end = group_start + _THOUSANDS_GROUP_SIZE
    return group_end <= len(text) and text[group_start:group_end].isdigit()


def _is_scientific_group_separator(char: str) -> bool:
    """Return True for group separators accepted by the old scientific regex."""
    return char in {",", "'", "\u00a0"} or char.isspace()


def _consume_scientific_exponent(text: str, marker_index: int) -> int | None:
    """Return the end index after a valid exponent, or None."""
    text_length = len(text)
    exponent_index = marker_index + 1
    if exponent_index < text_length and text[exponent_index] in "+-":
        exponent_index += 1

    exponent_start = exponent_index
    while exponent_index < text_length and text[exponent_index].isdigit():
        exponent_index += 1

    if exponent_index == exponent_start:
        return None

    return exponent_index


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
