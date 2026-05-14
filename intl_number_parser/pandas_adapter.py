"""Pandas vectorized integration for international number parsing.

This module provides the parse_series function that enables efficient
vectorized parsing of pandas Series containing international number formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

try:
    import numpy as np
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    # Create dummy modules for runtime when pandas is not available
    if not TYPE_CHECKING:

        class _DummyModule:
            def __getattr__(self, name: str) -> object:
                return None

        pd = _DummyModule()  # type: ignore[assignment]
        np = _DummyModule()  # type: ignore[assignment]

if TYPE_CHECKING:
    # These imports are only for type checking, not runtime
    import numpy as np
    import pandas as pd

from .core import parse_number
from .detector import LocaleDetector

# Constants for dataset sampling
_DEFAULT_DETECTION_SAMPLE_SIZE = 200

# Error message for missing pandas
_PANDAS_ERROR_MSG = (
    "pandas is required for parse_series functionality. "
    "Install with: pip install intl-number-parser[pandas]"
)


def _check_pandas_available() -> None:
    """Check if pandas is available, raise ImportError if not."""
    if not PANDAS_AVAILABLE:
        raise ImportError(_PANDAS_ERROR_MSG)


def parse_series(
    series: pd.Series,
    detector: LocaleDetector | None = None,
    *,
    sample_size: int = _DEFAULT_DETECTION_SAMPLE_SIZE,
) -> pd.Series:
    """Parse a pandas Series of international number strings to numeric values.

    This function vectorizes the parse_number functionality for efficient
    processing of large Series without Python loops where possible.

    Args:
        series: pandas Series containing string representations of numbers
                in any international format
        detector: Optional LocaleDetector for format detection. If None,
                 creates a temporary detector for autodetection based on
                 the series data.
        sample_size: Maximum number of valid values to sample when training
                     an automatic detector. Sampling is deterministic and
                     evenly distributed across the series.

    Returns:
        pandas Series with float64 dtype containing parsed numeric values.
        Invalid numbers are converted to NaN. Index and name are preserved.

    Raises:
        ImportError: If pandas is not installed

    Examples:
        >>> import pandas as pd
        >>> from intl_number_parser.pandas_adapter import parse_series
        >>> # US format
        >>> series = pd.Series(["1,234.56", "789.01", "12,345.67"])
        >>> parse_series(series)
        0     1234.56
        1      789.01
        2    12345.67
        dtype: float64

        >>> # European format
        >>> series = pd.Series(["1.234,56", "789,01", "12.345,67"])
        >>> parse_series(series)
        0     1234.56
        1      789.01
        2    12345.67
        dtype: float64

        >>> # With embedded text
        >>> series = pd.Series(["Price: $1,234.56", "Amount: €789.01"])
        >>> parse_series(series)
        0    1234.56
        1     789.01
        dtype: float64

    Performance:
        Designed to parse 10,000 values in under 0.5 seconds.
    """
    _check_pandas_available()
    if sample_size < 1:
        msg = "sample_size must be at least 1"
        raise ValueError(msg)

    # Handle empty series
    if len(series) == 0:
        return pd.Series([], dtype=np.float64, index=series.index, name=series.name)

    # Convert to string and handle NA values vectorially
    str_series = series.astype(str)

    # Create mask for valid (non-NA) values
    # Check for None, pd.NA, and pandas string representations of NA
    na_mask = (
        series.isna()
        | (str_series == "None")
        | (str_series == "<NA>")
        | (str_series.str.strip() == "")
    )

    # Prepare detector for batch processing
    if detector is None:
        # Create detector and train it on all valid values for accurate detection
        detector = LocaleDetector()
        valid_values = str_series[~na_mask]

        # Train detector with representative evidence from the full series.
        sample_values = _select_detection_sample(valid_values, sample_size)

        for value in sample_values:
            detector.ingest(str(value))

    # Initialize result array with NaN
    result_values = np.full(len(series), np.nan, dtype=np.float64)

    # Get valid indices and values
    valid_indices = np.where(~na_mask)[0]
    valid_values = str_series.iloc[valid_indices]

    # Process valid values
    if len(valid_values) > 0:
        # Use vectorized approach where possible
        parsed_values = _vectorized_parse(valid_values, detector)
        result_values[valid_indices] = parsed_values

    # Create result series with original index and name
    return pd.Series(
        result_values, index=series.index, name=series.name, dtype=np.float64
    )


def _select_detection_sample(valid_values: pd.Series, sample_size: int) -> pd.Series:
    """Select deterministic, evenly distributed values for detector training."""
    if len(valid_values) <= sample_size:
        return valid_values

    sample_indices = np.linspace(0, len(valid_values) - 1, sample_size, dtype=int)
    sample_indices = np.unique(sample_indices)
    sample = valid_values.iloc[sample_indices]
    return cast("pd.Series", sample)


def _vectorized_parse(str_series: pd.Series, detector: LocaleDetector) -> np.ndarray:
    """Vectorized parsing of string series using detector.

    Args:
        str_series: Series of string values to parse
        detector: LocaleDetector for format detection

    Returns:
        numpy array of parsed float values, with NaN for unparseable values
    """
    _check_pandas_available()

    # For optimal performance, we use pandas apply which is optimized
    # This is faster than pure Python loops and handles edge cases well
    def safe_parse(value: str) -> float:
        """Safely parse a single value, returning NaN on error."""
        try:
            result = parse_number(value, detector)
            # Convert int results to float for consistency
            return float(result)
        except (ValueError, TypeError):
            return float("nan")

    # Use pandas apply which is vectorized internally and faster than Python loops
    result = str_series.apply(safe_parse)
    # Convert to numpy array with explicit float64 dtype
    array_result: np.ndarray = np.array(result.values, dtype=np.float64)
    return array_result
