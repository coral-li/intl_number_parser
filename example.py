#!/usr/bin/env python3
# ruff: noqa: T201, PLR2004
"""
International Number Parser - Pandas Integration Examples

This file demonstrates the powerful pandas integration capabilities of the
intl-number-parser library with real-world examples you can run immediately.

Run this file with: python example.py
"""

import time

import pandas as pd

from intl_number_parser import LocaleDetector, parse_series


def demo_basic_parsing() -> None:
    """Demonstrate basic pandas Series parsing with multiple formats."""
    print("🚀 Basic Pandas Integration Demo")
    print("=" * 50)

    # Create sample data with different international formats
    data = pd.Series(
        [
            "1,234.56",  # US format
            "1.234,56",  # European format
            "1 234,56",  # French format
            "1'234.56",  # Swiss format
            "$1,000.00",  # With currency symbol
            "Price: €789.01",  # Embedded in text
            "Invalid text",  # Will become NaN
            "",  # Empty string -> NaN
            None,  # None -> NaN
        ],
        name="international_numbers",
    )

    print("Original Series:")
    print(data)
    print("\nAfter parsing with parse_series():")

    # Parse the series
    result = parse_series(data)
    print(result)
    print(f"\nDatatype: {result.dtype}")
    print(f"Series name preserved: {result.name}")


def demo_detector_training() -> None:
    """Demonstrate using LocaleDetector for better performance."""
    print("\n🎯 Locale Detector Training Demo")
    print("=" * 50)

    # European format dataset
    european_data = pd.Series(
        ["1.234,56", "789,01", "12.345,67", "999,99", "1.000.000,00"]
    )

    print("European format data:")
    print(european_data)

    # Method 1: Without detector (automatic detection)
    print("\nMethod 1: Automatic detection (slower)")
    start_time = time.time()
    result1 = parse_series(european_data)
    time1 = time.time() - start_time
    print(f"Result: {result1.tolist()}")
    print(f"Time: {time1:.4f} seconds")

    # Method 2: With pre-trained detector (faster)
    print("\nMethod 2: Pre-trained detector (faster)")
    detector = LocaleDetector()
    detector.ingest("1.234,56")  # Train with European format

    start_time = time.time()
    result2 = parse_series(european_data, detector)
    time2 = time.time() - start_time
    print(f"Result: {result2.tolist()}")
    print(f"Time: {time2:.4f} seconds")
    print(f"Speedup: {time1 / time2:.1f}x faster")

    # Show detector confidence
    print(f"\nDetector confidence: {detector.confidence:.1%}")
    if detector.best_candidate is not None:
        print(f"Detected decimal separator: '{detector.best_candidate.decimal}'")
        print(f"Detected thousands separator: '{detector.best_candidate.thousands}'")


def demo_dataframe_integration() -> None:
    """Demonstrate DataFrame integration with multiple columns."""
    print("\n📊 DataFrame Integration Demo")
    print("=" * 50)

    # Create a DataFrame with mixed international number formats
    df = pd.DataFrame(
        {
            "description": [
                "US Sales",
                "European Sales",
                "Swiss Sales",
                "French Sales",
                "Invalid Entry",
                "Japanese Sales",
            ],
            "amount_text": [
                "1,234.56",
                "1.234,56",
                "1'234.56",
                "1 234,56",
                "Not a number",
                "１２３４．５６",
            ],
            "currency": ["USD", "EUR", "CHF", "EUR", "USD", "JPY"],
        }
    )

    print("Original DataFrame:")
    print(df)

    # Parse the amount column
    df["amount_parsed"] = parse_series(df["amount_text"])

    print("\nAfter parsing amount_text column:")
    print(df)

    # Calculate some statistics
    print("\nStatistics:")
    print(f"Total amount: {df['amount_parsed'].sum():,.2f}")
    print(f"Average amount: {df['amount_parsed'].mean():,.2f}")
    print(f"Valid entries: {df['amount_parsed'].notna().sum()}/{len(df)}")


def demo_performance_large_dataset() -> None:
    """Demonstrate performance with large datasets."""
    print("\n⚡ Performance Demo - Large Dataset")
    print("=" * 50)

    # Create a large dataset (US format)
    print("Creating dataset of 10,000 numbers...")
    large_data = pd.Series([f"{i:,}.{i % 100:02d}" for i in range(1, 10001)])

    print(f"Sample data: {large_data.head().tolist()}")
    print(f"Dataset size: {len(large_data):,} numbers")

    # Parse with timing
    print("\nParsing 10,000 numbers...")
    start_time = time.time()
    result = parse_series(large_data)
    parse_time = time.time() - start_time

    print(f"✅ Completed in {parse_time:.3f} seconds")
    print(f"📈 Rate: {len(large_data) / parse_time:,.0f} numbers/second")
    print(f"🎯 Target: <0.5s (achieved: {'✅' if parse_time < 0.5 else '❌'})")
    print(f"Sample results: {result.head().tolist()}")


def demo_mixed_formats_autodetection() -> None:
    """Demonstrate automatic detection with mixed formats."""
    print("\n🌍 Mixed Format Auto-Detection Demo")
    print("=" * 50)

    # Mixed formats in the same series (unusual but handled gracefully)
    mixed_data = pd.Series(
        [
            "1,000.50",  # US format
            "2,000.75",  # US format
            "3,000.25",  # US format
            "1.500,99",  # European format (minority)
            "5,000.00",  # US format
            "6,000.33",  # US format
        ]
    )

    print("Mixed format data (mostly US, some European):")
    for i, val in enumerate(mixed_data):
        print(f"  {i}: {val}")

    # The detector will favor the majority format (US)
    result = parse_series(mixed_data)
    print("\nParsed results:")
    for i, (orig, parsed) in enumerate(zip(mixed_data, result)):
        status = "✅" if not pd.isna(parsed) else "❌"
        print(f"  {i}: {orig} → {parsed} {status}")


def demo_scientific_notation() -> None:
    """Demonstrate scientific notation support."""
    print("\n🔬 Scientific Notation Demo")
    print("=" * 50)

    scientific_data = pd.Series(
        [
            "1.23e4",  # Standard scientific
            "2.5E-3",  # Capital E, negative exponent
            "6.022e23",  # Avogadro's number
            "1,23e4",  # European decimal in scientific
            "-3.14e+2",  # Negative with explicit positive exponent
            "9.81E0",  # Zero exponent
        ]
    )

    print("Scientific notation data:")
    print(scientific_data)

    result = parse_series(scientific_data)
    print("\nParsed results:")
    print(result)

    # Show the actual values
    print("\nConverted to float for display:")
    for orig, parsed in zip(scientific_data, result):
        if not pd.isna(parsed):
            print(f"  {orig} → {float(parsed):,.2e}")


def demo_error_handling() -> None:
    """Demonstrate robust error handling."""
    print("\n🛡️ Error Handling Demo")
    print("=" * 50)

    problematic_data = pd.Series(
        [
            "1,234.56",  # Valid US format
            "",  # Empty string
            "   ",  # Whitespace only
            None,  # None value
            pd.NA,  # Pandas NA
            "Not a number",  # Invalid text
            "1,23,456.78",  # Invalid grouping
            "1.23.45.67",  # Multiple decimals
            "abc123def",  # Text with digits
            "123",  # Valid integer
        ]
    )

    print("Problematic data:")
    for i, val in enumerate(problematic_data):
        print(f"  {i}: {val!r}")

    result = parse_series(problematic_data)
    print("\nResults (invalid entries become NaN):")
    for i, (orig, parsed) in enumerate(zip(problematic_data, result)):
        status = "✅" if not pd.isna(parsed) else "❌"
        print(f"  {i}: {orig!r} → {parsed} {status}")

    print(f"\nValid entries: {result.notna().sum()}/{len(result)}")


def main() -> None:
    """Run all demonstration examples."""
    print("🌍 International Number Parser - Pandas Integration Examples")
    print("=" * 70)
    print("This demo shows the powerful pandas integration capabilities.")
    print("All examples use real data and can be run immediately.\n")

    # Run all demos
    demo_basic_parsing()
    demo_detector_training()
    demo_dataframe_integration()
    demo_performance_large_dataset()
    demo_mixed_formats_autodetection()
    demo_scientific_notation()
    demo_error_handling()

    print("\n" + "=" * 70)
    print("🎉 Demo completed! Try modifying the examples above.")
    print("📚 For more information, see the README.md file.")


if __name__ == "__main__":
    main()
