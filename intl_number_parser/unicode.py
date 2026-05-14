"""Unicode normalization and digit mapping utility.

This module provides utilities for normalizing Unicode numeric tokens
into canonical ASCII representation suitable for number parsing.
"""

from __future__ import annotations

import re
import unicodedata

_SIGN_MAPPINGS = {
    "\u2212": "-",  # Minus sign
    "\u207b": "-",  # Superscript minus
    "\u208b": "-",  # Subscript minus
    "\u207a": "+",  # Superscript plus
    "\u208a": "+",  # Subscript plus
}
_HARD_BOUNDARY = chr(0)
_BASIC_ALLOWED_CHARS = set("0123456789.,-+ '")
_ARABIC_PUNCTUATION = {
    "٬": "",  # Arabic thousands separator - remove (don't convert to comma)
    "٫": ".",  # Arabic decimal separator - convert to period
}


def normalize_token(token: str) -> str:
    """Convert any numeric token into a canonical ASCII representation.

    This function:
    1. Applies Unicode Normalisation Form KC (NFKC)
    2. Replaces non-breaking spaces and other Unicode space separators with ASCII space
    3. Maps all known Unicode digit blocks to ASCII 0-9
    4. Leaves ASCII digits and punctuation unchanged
    5. Filters out any characters not in the allowed set

    Args:
        token: The input token to normalize

    Returns:
        A string containing only [0-9 . , - + e E] and ASCII spaces

    Examples:
        >>> normalize_token("٤٬٥٦٧٫٨٩")
        '4567.89'
        >>> normalize_token("1\u00a0234,56")
        '1 234,56'
        >>> normalize_token("５．２")
        '5.2'
    """
    return _normalize_token(token, preserve_boundaries=False)


def _normalize_token_for_parsing(token: str) -> str:
    """Normalize a token while preserving hard boundaries for extraction."""
    return _normalize_token(token, preserve_boundaries=True)


def _normalize_token(token: str, *, preserve_boundaries: bool) -> str:
    """Normalize a token, optionally preserving hard token boundaries."""
    if not token:
        return ""

    # Step 1: Apply Unicode Normalisation Form KC (NFKC)
    normalized = unicodedata.normalize("NFKC", token)

    # Step 2: Check if input consists only of e/E and whitespace
    cleaned_input = "".join(char for char in normalized if char not in " \t\n\r")
    is_only_e_or_e = cleaned_input in ["e", "E", "eE", "Ee"]

    # Step 4: Build the result character by character
    result: list[str] = []

    def append_boundary() -> None:
        if not result or result[-1] != _HARD_BOUNDARY:
            result.append(_HARD_BOUNDARY)

    for i in range(len(normalized)):
        normalized_char = _normalize_char(normalized, i, is_only_e_or_e)
        if normalized_char is None:
            append_boundary()
        elif normalized_char:
            result.append(normalized_char)

    # Step 5: Post-process to handle spaces created by removing invalid characters
    return _finalize_normalized_result(
        "".join(result), normalized, preserve_boundaries=preserve_boundaries
    )


def _normalize_char(text: str, index: int, is_only_e_or_e: bool) -> str | None:
    """Return a normalized character, empty deletion, or None for a boundary."""
    mapped_char = _SIGN_MAPPINGS.get(text[index], text[index])

    if mapped_char in _ARABIC_PUNCTUATION:
        normalized_char = _ARABIC_PUNCTUATION[mapped_char]
    elif mapped_char in _BASIC_ALLOWED_CHARS:
        normalized_char = mapped_char
    elif mapped_char in ["e", "E"]:
        if is_only_e_or_e or _is_adjacent_to_digit(text, index):
            normalized_char = mapped_char
        else:
            normalized_char = None
    else:
        category = unicodedata.category(mapped_char)
        if category == "Zs":
            normalized_char = " "
        elif category == "Sc":
            normalized_char = ""
        else:
            digit_value = _try_get_unicode_digit(mapped_char)
            normalized_char = str(digit_value) if digit_value is not None else None

    return normalized_char


def _is_adjacent_to_digit(text: str, index: int) -> bool:
    """Check if character at index is adjacent to a digit."""
    if index > 0 and text[index - 1].isdigit():
        return True

    return index < len(text) - 1 and text[index + 1].isdigit()


def _finalize_normalized_result(
    text: str, normalized: str, *, preserve_boundaries: bool
) -> str:
    """Collapse boundaries, preserve requested marker visibility, and trim."""
    final_result = _collapse_token_boundaries(text)

    if preserve_boundaries:
        final_result = final_result.strip(_HARD_BOUNDARY)
    else:
        final_result = final_result.replace(_HARD_BOUNDARY, " ")

    # Check if we need to collapse spaces created by removing invalid characters
    # This is a heuristic: if the original input had no consecutive spaces,
    # but the result has consecutive spaces, then collapse them
    original_has_consecutive_spaces = any(
        normalized[i] == " " and normalized[i + 1] == " "
        for i in range(len(normalized) - 1)
    )

    if not original_has_consecutive_spaces:
        final_result = re.sub(r" {2,}", " ", final_result)

    # Trim leading and trailing spaces if they were created by removing invalid
    # characters. Check if the original input had leading/trailing spaces
    original_has_leading_space = normalized.startswith(" ")
    original_has_trailing_space = normalized.endswith(" ")

    if not original_has_leading_space and final_result.startswith(" "):
        final_result = final_result.lstrip(" ")
    if not original_has_trailing_space and final_result.endswith(" "):
        final_result = final_result.rstrip(" ")

    if not preserve_boundaries:
        final_result = _restore_outer_spaces(final_result, normalized)

    return final_result


def _restore_outer_spaces(text: str, normalized: str) -> str:
    """Preserve caller-provided leading and trailing spaces in public output."""
    leading_spaces = len(normalized) - len(normalized.lstrip(" "))
    trailing_spaces = len(normalized) - len(normalized.rstrip(" "))

    if leading_spaces > 0 and text.startswith(" "):
        text = " " * leading_spaces + text.lstrip(" ")
    if trailing_spaces > 0 and text.endswith(" "):
        text = text.rstrip(" ") + " " * trailing_spaces

    return text


def _collapse_token_boundaries(text: str) -> str:
    """Collapse boundary runs and surrounding spaces into one hard boundary."""
    boundary = re.escape(_HARD_BOUNDARY)
    return re.sub(rf"(?: *{boundary}+ *)+", _HARD_BOUNDARY, text)


def _try_get_unicode_digit(char: str) -> int | None:
    """Try to get the numeric value of a Unicode digit character."""
    try:
        return unicodedata.digit(char)
    except ValueError:
        return None
