"""Locale candidate definitions for international number format detection.

This module provides data structures for representing different locale-specific
number formatting conventions, enabling the automatic detection of number formats
through evidence accumulation.
"""

from dataclasses import dataclass, replace
from typing import List, Optional


@dataclass
class LocaleCandidate:
    """Represents a possible locale-specific number format for evidence-based detection.
    
    This class encapsulates the formatting rules for a specific locale's number
    representation, including decimal and thousands separators, grouping rules,
    and an accumulating score for format detection confidence.
    
    Attributes:
        decimal: The decimal separator character (e.g., '.', ',')
        thousands: The thousands separator character, or None if not used
                  (e.g., ',', '.', ' ', '\u00A0', "'", or None)
        group_size: Expected number of digits per thousands group (typically 3)
        score: Mutable evidence score for detection confidence (starts at 0)
               Increases when number format matches this candidate's rules,
               decreases when format violations are detected
    
    Examples:
        >>> # US/UK format: 1,234.56
        >>> us_format = LocaleCandidate(decimal=".", thousands=",", group_size=3, score=0)
        
        >>> # European format: 1.234,56  
        >>> eu_format = LocaleCandidate(decimal=",", thousands=".", group_size=3, score=0)
        
        >>> # Swiss format: 1'234.56
        >>> swiss_format = LocaleCandidate(decimal=".", thousands="'", group_size=3, score=0)
    """
    decimal: str
    thousands: Optional[str]
    group_size: int
    score: int


# The six most common international number format permutations
# covering the primary decimal/thousands separator combinations
COMMON_CANDIDATES: List[LocaleCandidate] = [
    # 1. US/UK format: 1,234.56 (comma thousands, period decimal)
    LocaleCandidate(
        decimal=".",
        thousands=",", 
        group_size=3,
        score=0
    ),
    
    # 2. European format: 1.234,56 (period thousands, comma decimal)
    LocaleCandidate(
        decimal=",",
        thousands=".",
        group_size=3, 
        score=0
    ),
    
    # 3. NBSP thousands + comma decimal: 1 234,56
    # Uses Unicode non-breaking space (U+00A0) for thousands separator
    LocaleCandidate(
        decimal=",",
        thousands="\u00A0",  # Non-breaking space
        group_size=3,
        score=0
    ),
    
    # 4. Regular space thousands + period decimal: 1 234.56
    LocaleCandidate(
        decimal=".",
        thousands=" ",  # Regular space
        group_size=3,
        score=0
    ),
    
    # 5. Swiss format: 1'234.56 (apostrophe thousands, period decimal)
    LocaleCandidate(
        decimal=".",
        thousands="'",  # Apostrophe
        group_size=3,
        score=0
    ),
    
    # 6. Regular space thousands + comma decimal: 1 234 567,89
    LocaleCandidate(
        decimal=",",
        thousands=" ",  # Regular space
        group_size=3,
        score=0
    )
]


def all_candidates() -> List[LocaleCandidate]:
    """Factory method returning fresh LocaleCandidate instances with reset scores.
    
    Creates independent copies of all common locale candidates with scores
    initialized to 0. This ensures that multiple detection sessions don't
    interfere with each other's evidence accumulation.
    
    Returns:
        A new list containing fresh LocaleCandidate instances, each with score=0.
        The list contains copies of all formats from COMMON_CANDIDATES but as
        independent objects that can be modified without affecting the originals.
        
    Examples:
        >>> candidates1 = all_candidates()
        >>> candidates2 = all_candidates()
        >>> candidates1[0].score = 10
        >>> candidates2[0].score  # Still 0 - independent instances
        0
        
        >>> len(all_candidates())
        6
        
    Note:
        Each call returns completely independent instances. Modifying the score
        or other attributes of candidates from one call will not affect
        candidates from other calls or the original COMMON_CANDIDATES list.
    """
    return [
        replace(candidate, score=0) 
        for candidate in COMMON_CANDIDATES
    ] 