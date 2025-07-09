"""Unicode normalization and digit mapping utility.

This module provides utilities for normalizing Unicode numeric tokens
into canonical ASCII representation suitable for number parsing.
"""

from __future__ import annotations

import re
import unicodedata


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
    if not token:
        return ""

    # Step 1: Apply Unicode Normalisation Form KC (NFKC)
    normalized = unicodedata.normalize("NFKC", token)

    # Step 2: Check if input consists only of e/E and whitespace
    cleaned_input = "".join(char for char in normalized if char not in " \t\n\r")
    is_only_e_or_e = cleaned_input in ["e", "E", "eE", "Ee"]

    # Step 3: Check which e/E characters are adjacent to digits
    def is_adjacent_to_digit(text: str, index: int) -> bool:
        """Check if character at index is adjacent to a digit."""
        # Check previous character
        if index > 0:
            prev_char = text[index - 1]
            if prev_char.isdigit():
                return True

        # Check next character
        if index < len(text) - 1:
            next_char = text[index + 1]
            if next_char.isdigit():
                return True

        return False

    # Step 4: Build the result character by character
    result = []

    # Basic allowed ASCII characters (without e and E for now)
    basic_allowed_chars = set("0123456789.,-+ ")

    # Arabic punctuation mappings
    arabic_punctuation = {
        "٬": "",  # Arabic thousands separator - remove (don't convert to comma)
        "٫": ".",  # Arabic decimal separator - convert to period
    }

    for i, char in enumerate(normalized):
        if char in arabic_punctuation:
            # Handle Arabic punctuation marks
            result.append(arabic_punctuation[char])
        elif char in basic_allowed_chars:
            # ASCII digit or allowed punctuation - keep as is
            result.append(char)
        elif char in ["e", "E"]:
            # Keep e and E only if they are adjacent to digits or input is only e/E
            if is_only_e_or_e or is_adjacent_to_digit(normalized, i):
                result.append(char)
        elif unicodedata.category(char) == "Zs":
            # Unicode space separator - replace with ASCII space
            result.append(" ")
        else:
            # Try to convert Unicode digit to ASCII
            digit_value = _try_get_unicode_digit(char)
            if digit_value is not None:
                result.append(str(digit_value))
            # Not a digit and not an allowed character - skip it

    # Step 5: Post-process to handle spaces created by removing invalid characters
    final_result = "".join(result)

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

    return final_result


def _try_get_unicode_digit(char: str) -> int | None:
    """Try to get the numeric value of a Unicode digit character."""
    try:
        return unicodedata.digit(char)
    except ValueError:
        return None
