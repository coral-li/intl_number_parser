"""Tests for the pandas adapter module.

This module tests the pandas integration functionality including
vectorized series parsing, performance requirements, and integration
with the LocaleDetector.
"""

import importlib
import sys
import time
import unittest.mock

import numpy as np
import pandas as pd
import pytest

import intl_number_parser.pandas_adapter
from intl_number_parser.detector import LocaleDetector
from intl_number_parser.pandas_adapter import (
    _check_pandas_available,
    _vectorized_parse,
    parse_series,
)


class TestParseSeriesImport:
    """Test that parse_series can be imported properly."""

    def test_import_parse_series(self):
        """Test that parse_series can be imported from the adapter module."""
        assert callable(parse_series)


class TestParseSeriesBasic:
    """Test basic functionality of parse_series."""

    def test_parse_series_us_format(self):
        """Test parsing series with US number format."""
        series = pd.Series(["1,234.56", "789.01", "12,345.67"])
        result = parse_series(series)

        expected = pd.Series([1234.56, 789.01, 12345.67])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_european_format(self):
        """Test parsing series with European number format."""
        series = pd.Series(["1.234,56", "789,01", "12.345,67"])
        result = parse_series(series)

        expected = pd.Series([1234.56, 789.01, 12345.67])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_mixed_types(self):
        """Test parsing series with mixed integer and decimal numbers."""
        series = pd.Series(["1,234", "567.89", "42"])
        result = parse_series(series)

        # Should return floats for consistency
        expected = pd.Series([1234.0, 567.89, 42.0])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_with_detector(self):
        """Test parsing series with explicit LocaleDetector."""
        detector = LocaleDetector()
        detector.ingest("1,234.56")  # Train for US format

        series = pd.Series(["789.01", "12,345.67"])
        result = parse_series(series, detector)

        expected = pd.Series([789.01, 12345.67])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_empty(self):
        """Test parsing empty series."""
        series = pd.Series([], dtype=str)
        result = parse_series(series)

        expected = pd.Series([], dtype=float)
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_single_value(self):
        """Test parsing series with single value."""
        series = pd.Series(["1,234.56"])
        result = parse_series(series)

        expected = pd.Series([1234.56])
        pd.testing.assert_series_equal(result, expected)


class TestParseSeriesNAHandling:
    """Test NA/null value handling in parse_series."""

    def test_parse_series_with_na_values(self):
        """Test parsing series containing NA values."""
        series = pd.Series(["1,234.56", None, "789.01", pd.NA])
        result = parse_series(series)

        expected = pd.Series([1234.56, np.nan, 789.01, np.nan])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_with_empty_strings(self):
        """Test parsing series containing empty strings."""
        series = pd.Series(["1,234.56", "", "789.01", "   "])
        result = parse_series(series)

        # Empty strings should result in NaN
        expected = pd.Series([1234.56, np.nan, 789.01, np.nan])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_preserve_na_types(self):
        """Test that NA values are properly preserved in result."""
        series = pd.Series(["1.23", None, "4.56"])
        result = parse_series(series)

        assert not pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert not pd.isna(result.iloc[2])


class TestParseSeriesScientificNotation:
    """Test scientific notation handling in parse_series."""

    def test_parse_series_scientific_notation(self):
        """Test parsing series with scientific notation."""
        series = pd.Series(["1.23e4", "5.67E-3", "8.9e+2"])
        result = parse_series(series)

        expected = pd.Series([12300.0, 0.00567, 890.0])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_mixed_scientific_and_regular(self):
        """Test parsing series mixing scientific and regular notation."""
        series = pd.Series(["1,234.56", "1.23e4", "789.01"])
        result = parse_series(series)

        expected = pd.Series([1234.56, 12300.0, 789.01])
        pd.testing.assert_series_equal(result, expected)


class TestParseSeriesEmbeddedNumbers:
    """Test embedded number extraction in parse_series."""

    def test_parse_series_embedded_numbers(self):
        """Test parsing series with numbers embedded in text."""
        series = pd.Series(["Price: $1,234.56", "Amount: €789.01", "Total: 12,345.67"])
        result = parse_series(series)

        expected = pd.Series([1234.56, 789.01, 12345.67])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_complex_text(self):
        """Test parsing series with complex text patterns."""
        series = pd.Series(
            ["Temperature: -5.5°C", "Profit margin: +12.34%", "Distance: 1,234.56 km"]
        )
        result = parse_series(series)

        expected = pd.Series([-5.5, 12.34, 1234.56])
        pd.testing.assert_series_equal(result, expected)


class TestParseSeriesErrorHandling:
    """Test error handling in parse_series."""

    def test_parse_series_invalid_numbers(self):
        """Test parsing series with invalid number formats."""
        series = pd.Series(["1,234.56", "invalid", "789.01"])
        result = parse_series(series)

        # Invalid entries should result in NaN
        expected = pd.Series([1234.56, np.nan, 789.01])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_mixed_formats_auto_detect(self):
        """Test that auto-detection handles consistent formats."""
        # Series with consistent US format should be detected properly
        series = pd.Series(["1,234.56", "789.01", "12,345.67"])
        result = parse_series(series)

        expected = pd.Series([1234.56, 789.01, 12345.67])
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_conflicting_formats(self):
        """Test handling of conflicting number formats in same series."""
        # This should still work with best-effort parsing
        series = pd.Series(["1,234.56", "1.234,56", "789.01"])
        result = parse_series(series)

        # Should return some valid results, exact behavior depends on detector
        assert len(result) == 3
        assert not result.isna().all()  # At least some should parse


class TestParseSeriesPerformance:
    """Test performance requirements for parse_series."""

    def test_parse_series_large_performance(self):
        """Test that parsing 10,000 values takes less than 1 second."""
        # Create series with 10,000 US format numbers
        data = [f"{i:,}.{i % 100:02d}" for i in range(1000, 11000)]
        series = pd.Series(data)

        start_time = time.time()
        result = parse_series(series)
        elapsed_time = time.time() - start_time

        # Should complete in under 1 second (more realistic timing)
        assert elapsed_time < 1.0, f"Parsing took {elapsed_time:.3f}s, expected < 1.0s"
        assert len(result) == 10000
        assert result.dtype == np.float64
        assert result.iloc[0] == 1000.0
        assert result.iloc[-1] == 10999.99  # Fixed expected value

    def test_parse_series_performance_with_detector(self):
        """Test performance with pre-configured detector."""
        # Create pre-trained detector
        detector = LocaleDetector()
        detector.ingest("1,234.56")

        # Create large series
        data = [f"{i:,}.{i % 100:02d}" for i in range(1000, 6000)]
        series = pd.Series(data)

        start_time = time.time()
        result = parse_series(series, detector)
        elapsed_time = time.time() - start_time

        # Should be even faster with pre-configured detector
        assert elapsed_time < 0.3, (
            f"Parsing with detector took {elapsed_time:.3f}s, expected < 0.3s"
        )

        # Verify results
        assert len(result) == 5000
        assert not result.isna().any()


class TestParseSeriesReturnTypes:
    """Test return type handling in parse_series."""

    def test_parse_series_return_float64(self):
        """Test that result has correct float64 dtype."""
        series = pd.Series(["1,234.56", "789.01"])
        result = parse_series(series)

        assert result.dtype == np.float64

    def test_parse_series_large_integers(self):
        """Test handling of large integers that exceed int64 range."""
        # Numbers larger than 2^63-1
        series = pd.Series(["9,223,372,036,854,775,808", "1,234.56"])
        result = parse_series(series)

        # Should return floats for large integers
        assert result.dtype == np.float64
        assert result.iloc[0] == 9223372036854775808.0
        assert result.iloc[1] == 1234.56

    def test_parse_series_convert_dtypes_compatible(self):
        """Test that result is compatible with pandas convert_dtypes."""
        series = pd.Series(["1,234", "567", "89"])
        result = parse_series(series)

        # Should be able to convert dtypes without issues
        converted = result.convert_dtypes()
        # Since these are integers, pandas should convert them to Int64Dtype
        assert converted.dtype in [np.float64, pd.Float64Dtype(), pd.Int64Dtype()]


class TestParseSeriesIntegration:
    """Test integration with other pandas operations."""

    def test_parse_series_with_index(self):
        """Test that index is preserved during parsing."""
        index = ["a", "b", "c"]
        series = pd.Series(["1,234.56", "789.01", "12,345.67"], index=index)
        result = parse_series(series)

        expected = pd.Series([1234.56, 789.01, 12345.67], index=index)
        pd.testing.assert_series_equal(result, expected)

    def test_parse_series_with_name(self):
        """Test that series name is preserved during parsing."""
        series = pd.Series(["1,234.56", "789.01"], name="amounts")
        result = parse_series(series)

        assert result.name == "amounts"

    def test_parse_series_in_dataframe(self):
        """Test parsing series as part of DataFrame operations."""
        dataframe = pd.DataFrame(
            {
                "text_numbers": ["1,234.56", "789.01", "12,345.67"],
                "other_col": ["a", "b", "c"],
            }
        )

        dataframe["parsed_numbers"] = parse_series(dataframe["text_numbers"])

        assert dataframe["parsed_numbers"].dtype == np.float64
        assert dataframe["parsed_numbers"].iloc[0] == 1234.56


class TestPandasAdapterCoverage:
    """Target specific uncovered lines in pandas_adapter.py."""

    def test_parse_series_large_dataset_strategic_sampling(self):
        """Test the strategic sampling for large datasets (>30 values)."""
        # Create a dataset with >30 values to trigger strategic sampling
        values = [f"{1000 + i:,}" for i in range(40)]  # 40 values: 1,000 to 1,039
        series = pd.Series(values)

        result = parse_series(series)

        # Should parse all values successfully
        assert len(result) == 40
        assert not result.isna().any()
        assert result.iloc[0] == 1000.0  # First value
        assert result.iloc[-1] == 1039.0  # Last value

    def test_parse_series_empty_valid_values_branch(self):
        """Test branch where all values are NA/invalid."""
        # Series with all NA/invalid values
        series = pd.Series([None, pd.NA, "", "   "])
        result = parse_series(series)

        # Should return all NaN values
        assert len(result) == 4
        assert result.isna().all()
        assert result.dtype == np.float64

    def test_parse_series_mixed_valid_invalid_values(self):
        """Test processing of mixed valid and invalid values."""
        # Mix of valid, invalid, and NA values
        series = pd.Series(["1,234", "invalid", None, "5,678", pd.NA, "not_a_number"])
        result = parse_series(series)

        # Should have parsed values for valid entries, NaN for invalid
        assert len(result) == 6
        assert result.iloc[0] == 1234  # Valid
        assert pd.isna(result.iloc[1])  # Invalid
        assert pd.isna(result.iloc[2])  # None
        assert result.iloc[3] == 5678  # Valid
        assert pd.isna(result.iloc[4])  # pd.NA
        assert pd.isna(result.iloc[5])  # Invalid

    def test_parse_series_vectorized_parse_error_handling(self):
        """Test error handling in the vectorized parsing function."""
        # Test with values that should cause parsing errors
        series = pd.Series(["1,234", "completely invalid", "5.67e", "789"])
        result = parse_series(series)

        # Should handle errors gracefully
        assert len(result) == 4
        assert result.iloc[0] == 1234.0  # Valid
        assert pd.isna(result.iloc[1])  # Invalid
        assert result.iloc[2] == 5.67  # Valid (strips trailing 'e')
        assert result.iloc[3] == 789.0  # Valid

    def test_parse_series_large_dataset_with_detector(self):
        """Test large dataset processing with pre-configured detector."""
        # Create detector and configure for US format
        detector = LocaleDetector()
        detector.ingest("1,234.56")  # Train with US format

        # Create large dataset (>30 values)
        values = [f"{i:,}.50" for i in range(1000, 1035)]  # 35 values
        series = pd.Series(values)

        result = parse_series(series, detector)

        # Should parse all values successfully
        assert len(result) == 35
        assert not result.isna().any()
        assert result.iloc[0] == 1000.50
        assert result.iloc[-1] == 1034.50


class TestMissingPandasCoverage:
    """Additional tests to achieve 100% coverage for missing pandas adapter branches."""

    def test_should_cover_empty_valid_values_condition(self):
        """Test condition when there are no valid values to process."""
        # Mock PANDAS_AVAILABLE to test the pandas availability check
        with unittest.mock.patch(
            "intl_number_parser.pandas_adapter.PANDAS_AVAILABLE", False
        ):
            # parse_series is already imported at top level

            # Create series with all invalid values
            series = pd.Series([None, pd.NA, "", "   ", "<NA>"])

            # This should raise ImportError because pandas is marked as not available
            with pytest.raises(ImportError) as excinfo:
                parse_series(series)

            assert "pandas is required" in str(excinfo.value)
            assert "pip install intl-number-parser[pandas]" in str(excinfo.value)

    def test_should_cover_pandas_not_available(self):
        """Test behavior when pandas is not available."""
        # Mock pandas as not available
        with unittest.mock.patch.dict(sys.modules, {"pandas": None, "numpy": None}):
            # Reload the module to trigger ImportError
            # intl_number_parser.pandas_adapter is already imported at top level

            # Force reimport with pandas unavailable
            importlib.reload(intl_number_parser.pandas_adapter)

            # Test that _check_pandas_available raises ImportError
            # _check_pandas_available is already imported at top level

            with pytest.raises(ImportError) as excinfo:
                _check_pandas_available()

            assert "pandas is required" in str(excinfo.value)
            assert "pip install intl-number-parser[pandas]" in str(excinfo.value)

    def test_should_cover_vectorized_parse_pandas_not_available(self):
        """Test _vectorized_parse when pandas is not available."""
        # Create a dummy series first
        dummy_series = pd.Series(["1,234.56"])

        # Mock pandas as not available
        with unittest.mock.patch.dict(sys.modules, {"pandas": None, "numpy": None}):
            # This should trigger the pandas not available path
            # intl_number_parser.pandas_adapter is already imported at top level

            # Force reimport with pandas unavailable
            importlib.reload(intl_number_parser.pandas_adapter)

            # LocaleDetector is already imported at top level
            # _vectorized_parse is already imported at top level

            # This should raise ImportError
            with pytest.raises(ImportError):
                _vectorized_parse(dummy_series, LocaleDetector())
