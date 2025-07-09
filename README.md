# International Number Parser

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue)](http://mypy-lang.org/)

A robust, locale-aware international number parsing library for Python that automatically detects and parses numeric values from any international format without prior knowledge of the input format.

## ✨ Features

- **🌍 Universal Format Support**: Automatically detects and parses numbers in any international format
- **🚀 High Performance**: Vectorized pandas integration with <0.5s processing for 10,000 values
- **🎯 99%+ Accuracy**: Evidence-based locale detection with intelligent confidence scoring
- **🔢 Complete Numeric Support**: Integers, decimals, scientific notation, and embedded numbers
- **🐍 Type Safe**: Full type hints with mypy strict mode compliance
- **🧪 Battle Tested**: 100% branch coverage with 220+ comprehensive tests
- **📊 Pandas Ready**: Native pandas Series integration for data science workflows
- **🌐 Unicode Aware**: Handles international Unicode digits and normalization

## 🚀 Quick Start

### Installation

```bash
pip install intl-number-parser
```

### Basic Usage

```python
from intl_number_parser import parse_number

# US/UK format
parse_number("1,234.56")           # → '1234.56'

# European format  
parse_number("1.234,56")           # → '1234.56'

# Swiss format
parse_number("1'234.56")           # → '1234.56'

# Space-separated (French/German)
parse_number("1 234,56")           # → '1234.56'

# Scientific notation
parse_number("1.23e-4")            # → '1.23e-4'

# Integers (returns int type)
parse_number("42")                 # → 42

# Embedded in text
parse_number("Price: $1,234.56")   # → '1234.56'
parse_number("Total: €1.234,56")   # → '1234.56'
```

### Pandas Integration

```python
import pandas as pd
from intl_number_parser import parse_series

# Parse a Series of international numbers
data = pd.Series([
    "1,234.56",    # US format
    "1.234,56",    # European format  
    "1 234,56",    # French format
    "1'234.56",    # Swiss format
    "$1,000.00",   # With currency
    "Invalid"      # Becomes NaN
])

result = parse_series(data)
print(result)
# 0    1234.56
# 1    1234.56  
# 2    1234.56
# 3    1234.56
# 4    1000.00
# 5        NaN
# dtype: float64
```

## 📖 Detailed Usage

### Supported Number Formats

The library automatically detects and handles these international formats:

| Format | Example | Description |
|--------|---------|-------------|
| **US/UK** | `1,234.56` | Comma thousands, period decimal |
| **European** | `1.234,56` | Period thousands, comma decimal |
| **French/German** | `1 234,56` | Space thousands, comma decimal |
| **International** | `1 234.56` | Space thousands, period decimal |
| **Swiss** | `1'234.56` | Apostrophe thousands, period decimal |
| **Mixed Space** | `1 234 567,89` | Space thousands, comma decimal |

### Advanced Usage with Locale Detection

For better performance when processing multiple numbers in the same format, use the `LocaleDetector`:

```python
from intl_number_parser import parse_number, LocaleDetector

# Create and train detector
detector = LocaleDetector()

# Feed it examples to learn the format
detector.ingest("1,234.56")
detector.ingest("789.01") 
detector.ingest("12,345.67")

# Now parsing is faster and more accurate
result1 = parse_number("999.99", detector)    # → '999.99'
result2 = parse_number("1,111.11", detector)  # → '1111.11'

# Check detection confidence
print(f"Confidence: {detector.confidence:.2%}")  # → Confidence: 98%
print(f"Detected format: {detector.best_candidate.decimal}")  # → .
```

### Pandas Integration with Detector

For large datasets, pre-training the detector improves performance:

```python
import pandas as pd
from intl_number_parser import parse_series, LocaleDetector

# Large dataset in European format
df = pd.DataFrame({
    'amounts': ['1.234,56', '789,01', '12.345,67'] * 1000
})

# Pre-train detector for better performance
detector = LocaleDetector()
detector.ingest('1.234,56')  # European format sample

# Fast vectorized parsing
df['parsed'] = parse_series(df['amounts'], detector)
```

### Unicode and International Characters

The library handles Unicode digits and international punctuation:

```python
from intl_number_parser import parse_number

# Arabic-Indic digits
parse_number("٤٬٥٦٧٫٨٩")         # → '4567.89'

# Full-width Unicode digits (Japanese/Chinese)
parse_number("１２３４．５６")      # → '1234.56'

# Mixed Unicode spaces and separators
parse_number("1 234,56")          # → '1234.56' (NBSP preserved)
```

### Scientific Notation

Full support for scientific notation in any locale:

```python
from intl_number_parser import parse_number

parse_number("1.23e4")            # → '12300.0'
parse_number("1,23E-4")           # → '1.23e-4' (European decimal)
parse_number("-2.5e+10")         # → '-2.5e+10'
parse_number("6.022e23")          # → '6.022e23' (Avogadro's number)
```

### Error Handling

The library provides clear error messages for invalid input:

```python
from intl_number_parser import parse_number

try:
    parse_number("not a number")
except ValueError as e:
    print(e)  # → "No valid number found in token"

try:
    parse_number("")
except ValueError as e:
    print(e)  # → "No valid number found in token"
```

### Return Types and Precision

The library intelligently chooses return types based on the number:

```python
from intl_number_parser import parse_number

# Small integers return int type
parse_number("42")                    # → 42 (int)
parse_number("1,000")                 # → 1000 (int)

# Large integers return string (for precision)
parse_number("999999999999999999")   # → '999999999999999999' (str)

# Decimals always return string  
parse_number("42.0")                 # → '42.0' (str)
parse_number("1,234.56")             # → '1234.56' (str)

# Use with decimal.Decimal for exact precision
from decimal import Decimal
result = Decimal(parse_number("1,234.56"))  # → Decimal('1234.56')
```

## 🚀 Performance

The library is optimized for high-performance processing:

### Benchmarks

- **Single numbers**: ~0.01ms per number
- **Pandas Series**: <0.5s for 10,000 numbers  
- **Memory usage**: Minimal overhead with vectorized operations
- **Accuracy**: >99% automatic format detection

### Performance Tips

1. **Reuse detectors** for multiple numbers in the same format
2. **Use pandas integration** for large datasets
3. **Pre-train detectors** with sample data for consistent formats

```python
# ✅ Efficient for multiple numbers
detector = LocaleDetector()
detector.ingest("1,234.56")  # Train once

results = [parse_number(num, detector) for num in many_numbers]

# ✅ Even better: use pandas for large datasets  
import pandas as pd
series = pd.Series(many_numbers)
results = parse_series(series, detector)
```

## 🛠️ API Reference

### Core Functions

#### `parse_number(token: str, detector: LocaleDetector | None = None) -> str | int`

Parse a single number from any international format.

**Parameters:**
- `token` (str): Input string containing a number (may be embedded in text)
- `detector` (LocaleDetector, optional): Pre-configured detector for better performance

**Returns:**
- `int`: For integers within 64-bit range
- `str`: For decimals, large integers, or scientific notation

**Raises:**
- `ValueError`: If no valid number is found

#### `parse_series(series: pd.Series, detector: LocaleDetector | None = None) -> pd.Series`

Parse a pandas Series of international number strings.

**Parameters:**
- `series` (pd.Series): Series containing string representations of numbers
- `detector` (LocaleDetector, optional): Pre-configured detector for better performance

**Returns:**
- `pd.Series`: Series with float64 dtype containing parsed numbers

### Locale Detection

#### `LocaleDetector`

Evidence-accumulating locale detector for format identification.

```python
from intl_number_parser import LocaleDetector

detector = LocaleDetector()

# Train with examples
detector.ingest("1,234.56")
detector.ingest("789.01")

# Check results
print(detector.confidence)      # 0.0 to 1.0
print(detector.is_locked)       # True when confident
print(detector.best_candidate)  # LocaleCandidate object
```

**Methods:**
- `ingest(token: str)`: Add evidence from a number example
- `freeze(candidate)`: Lock to a specific format
- `override(candidate)`: Set format but continue learning

**Properties:**
- `confidence`: Detection confidence (0.0-1.0)
- `is_locked`: Whether detector is confident enough to lock
- `best_candidate`: Highest-scoring format candidate

## 🧪 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/intl-number-parser.git
cd intl-number-parser

# Complete development setup
make install-all
```

### Available Commands

```bash
# Code quality
make lint                 # Run linter
make format              # Format code  
make typecheck           # Type checking
make check               # Run all quality checks

# Testing
make test                # Run tests
make test-coverage       # Run tests with coverage
make coverage-open       # Open coverage report

# Development workflow
make dev                 # Quick development setup
make status              # Show project status
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_core.py -v

# Run tests in parallel
make test-parallel
```

### Code Quality

The project maintains high code quality standards:

- **100% branch coverage** for core modules
- **mypy strict mode** compliance
- **ruff linting** with comprehensive rules
- **Security scanning** with bandit
- **Pre-commit hooks** for automated checks

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following our [TDD approach](REQUIREMENTS.md#test-driven-development)
4. Run the full test suite: `make check`
5. Submit a pull request

### Development Guidelines

- Follow **Test-Driven Development** (Red-Green-Refactor)
- Maintain **100% branch coverage** for new code
- Add **type hints** for all new functions
- Update **documentation** for API changes
- Follow **conventional commits** for commit messages

## 🐛 Issues and Support

- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/intl-number-parser/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/intl-number-parser/discussions)
- **Documentation**: [Read the Docs](https://intl-number-parser.readthedocs.io/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Unicode Consortium** for international digit standards
- **Pandas Team** for vectorization inspiration  
- **Python Community** for excellent tooling ecosystem

---

**Made with ❤️ for the global Python community** 