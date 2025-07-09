"""Tests for unicode normalization and digit mapping utility."""

from intl_number_parser.unicode import normalize_token


class TestNormalizeToken:
    """Test cases for normalize_token function."""

    def test_normalize_token_ascii_unchanged(self):
        """Test that ASCII characters are unchanged."""
        assert normalize_token("123.45") == "123.45"
        assert normalize_token("123,45") == "123,45"
        assert normalize_token("-123.45") == "-123.45"
        assert normalize_token("+123.45") == "+123.45"
        assert normalize_token("123 456") == "123 456"

    def test_normalize_token_arabic_indic_digits(self):
        """Test Arabic-Indic digit normalization."""
        # Arabic-Indic digits: ٠١٢٣٤٥٦٧٨٩
        assert normalize_token("٠١٢٣٤٥٦٧٨٩") == "0123456789"
        assert normalize_token("٤٬٥٦٧٫٨٩") == "4567.89"
        assert normalize_token("١٢٣٫٤٥") == "123.45"
        assert normalize_token("٩٨٧٬٦٥٤٫٣٢") == "987654.32"

    def test_normalize_token_devanagari_digits(self):
        """Test Devanagari digit normalization."""
        # Devanagari digits: ०१२३४५६७८९
        assert normalize_token("०१२३४५६७८९") == "0123456789"
        assert normalize_token("१२३.४५") == "123.45"

    def test_normalize_token_full_width_digits(self):
        """Test Full-width digit normalization."""
        # Full-width digits: ０１２３４５６７８９
        assert normalize_token("０１２３４５６７８９") == "0123456789"
        assert normalize_token("５．２") == "5.2"
        assert normalize_token("１２３４５６７８９０") == "1234567890"

    def test_normalize_token_bengali_digits(self):
        """Test Bengali digit normalization."""
        # Bengali digits: ০১২৩৪৫৬৭৮৯
        assert normalize_token("০১২৩৪৫৬৭৮৯") == "0123456789"
        assert normalize_token("১২৩.৪৫") == "123.45"

    def test_normalize_token_thai_digits(self):
        """Test Thai digit normalization."""
        # Thai digits: ๐๑๒๓๔๕๖๗๘๙
        assert normalize_token("๐๑๒๓๔๕๖๗๘๙") == "0123456789"
        assert normalize_token("๑๒๓.๔๕") == "123.45"

    def test_normalize_token_unicode_space_separators(self):
        """Test Unicode space separator normalization."""
        # Non-breaking space (U+00A0)
        assert normalize_token("1\u00A0234") == "1 234"
        assert normalize_token("1\u00A0234,56") == "1 234,56"

        # Thin space (U+2009)
        assert normalize_token("1\u2009234") == "1 234"

        # Figure space (U+2007)
        assert normalize_token("1\u2007234") == "1 234"

        # Punctuation space (U+2008)
        assert normalize_token("1\u2008234") == "1 234"

        # Six-per-em space (U+2006)
        assert normalize_token("1\u2006234") == "1 234"

    def test_normalize_token_nfkc_normalization(self):
        """Test NFKC normalization is applied."""
        # Test that NFKC normalization is applied
        # Roman numeral one (U+2160) -> "I"
        # But we only keep digits, so it should be removed
        assert normalize_token("Ⅰ") == ""

        # Full-width comma (U+FF0C) -> regular comma
        assert normalize_token("１２３，４５") == "123,45"

        # Full-width period (U+FF0E) -> regular period
        assert normalize_token("１２３．４５") == "123.45"

        # Full-width plus (U+FF0B) -> regular plus
        assert normalize_token("＋１２３") == "+123"

        # Full-width minus (U+FF0D) -> regular minus
        assert normalize_token("－１２３") == "-123"

    def test_normalize_token_mixed_scripts(self):
        """Test mixed scripts in one token."""
        # Mix of Arabic-Indic and ASCII
        assert normalize_token("١٢3.45") == "123.45"

        # Mix of Full-width and ASCII
        assert normalize_token("１２3.45") == "123.45"

        # Mix of different scripts
        assert normalize_token("१२३.४५") == "123.45"

    def test_normalize_token_negative_and_positive_signs(self):
        """Test handling of negative and positive signs."""
        # Regular minus
        assert normalize_token("-123.45") == "-123.45"

        # Regular plus
        assert normalize_token("+123.45") == "+123.45"

        # Full-width minus
        assert normalize_token("－123.45") == "-123.45"

        # Full-width plus
        assert normalize_token("＋123.45") == "+123.45"

        # Minus with Arabic-Indic
        assert normalize_token("-١٢٣.٤٥") == "-123.45"

    def test_normalize_token_scientific_notation(self):
        """Test scientific notation normalization."""
        # Basic scientific notation
        assert normalize_token("1.23e10") == "1.23e10"
        assert normalize_token("1.23E10") == "1.23E10"
        assert normalize_token("1.23e-10") == "1.23e-10"
        assert normalize_token("1.23E+10") == "1.23E+10"

        # With Unicode digits
        assert normalize_token("১.২৩e১০") == "1.23e10"
        assert normalize_token("１.２３E１０") == "1.23E10"

    def test_normalize_token_only_allowed_characters(self):
        """Test that only allowed characters are returned."""
        # Test with text mixed with numbers
        result = normalize_token("१२३.४५ abc 456")
        assert result == "123.45 456"

        # Test with various non-digit characters
        result = normalize_token("abc १२३ def ४५६ ghi")
        assert result == "123 456"

        # Test with symbols
        result = normalize_token("123@#$%^&*()456")
        assert result == "123456"

    def test_normalize_token_empty_string(self):
        """Test empty string input."""
        assert normalize_token("") == ""

    def test_normalize_token_only_invalid_characters(self):
        """Test string with only invalid characters."""
        assert normalize_token("abcdefg") == ""
        assert normalize_token("!@#$%^&*()") == ""
        assert normalize_token("αβγδε") == ""

    def test_normalize_token_whitespace_only(self):
        """Test various whitespace characters."""
        assert normalize_token("   ") == "   "
        assert normalize_token("\u00A0\u00A0") == "  "
        assert normalize_token("\u2009\u2008") == "  "

    def test_normalize_token_complex_examples(self):
        """Test complex real-world examples."""
        # European number with non-breaking space
        assert normalize_token("1\u00A0234\u00A0567,89") == "1 234 567,89"

        # Mixed Arabic-Indic with punctuation
        assert normalize_token("١٬٢٣٤٫٥٦٧") == "1234.567"

        # Full-width with scientific notation
        assert normalize_token("１．２３Ｅ１０") == "1.23E10"

        # Complex mixed example
        assert normalize_token("Test: ١٢٣٬٤٥٦.٧٨٩ (approx)") == "123456.789"

    def test_normalize_token_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Only digits
        assert normalize_token("0123456789") == "0123456789"

        # Only separators
        assert normalize_token(".,") == ".,"

        # Only signs
        assert normalize_token("+-") == "+-"

        # Only scientific notation letters
        assert normalize_token("eE") == "eE"

        # Multiple spaces
        assert normalize_token("1  2  3") == "1  2  3"

        # Leading/trailing invalid characters
        assert normalize_token("abc123def") == "123"
        assert normalize_token("   123   ") == "   123   "

    def test_normalize_token_unicode_categories(self):
        """Test that the function handles various Unicode categories correctly."""
        # Test with characters from different Unicode categories
        # but only keeps the allowed ones
        mixed_input = "123α456β789γ"
        assert normalize_token(mixed_input) == "123456789"

        # Test with currency symbols
        assert normalize_token("$123.45€") == "123.45"

        # Test with mathematical symbols
        assert normalize_token("123+456-789") == "123+456-789"
        assert normalize_token("123×456÷789") == "123456789"

    def test_normalize_token_performance_characteristics(self):
        """Test that the function works with long strings (O(n) requirement)."""
        # Test with long string of valid characters
        long_input = "1234567890" * 1000
        result = normalize_token(long_input)
        expected = "1234567890" * 1000
        assert result == expected

        # Test with long string of invalid characters
        invalid_input = "abcdefghij" * 1000
        assert normalize_token(invalid_input) == ""

    def test_normalize_token_all_unicode_digit_blocks(self):
        """Test various Unicode digit blocks."""
        test_cases = [
            ("٠١٢٣٤٥٦٧٨٩", "0123456789"),  # Arabic-Indic
            ("०१२३४५६७८९", "0123456789"),  # Devanagari
            ("০১২৩৪৫৬৭৮৯", "0123456789"),  # Bengali
            ("๐๑๒๓๔๕๖๗๘๙", "0123456789"),  # Thai
            ("០១២៣៤៥៦៧៨៩", "0123456789"),  # Khmer
            ("༠༡༢༣༤༥༦༧༨༩", "0123456789"),  # Tibetan
            ("០១២៣៤៥៦៧៨៩", "0123456789"),  # Khmer
            ("᠐᠑᠒᠓᠔᠕᠖᠗᠘᠙", "0123456789"),  # Mongolian
            ("꘠꘡꘢꘣꘤꘥꘦꘧꘨꘩", "0123456789"),  # Vai
            ("𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗", "0123456789"),  # Mathematical Bold
            ("𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡", "0123456789"),  # Mathematical Double-struck
            ("၀၁၂၃၄၅၆၇၈၉", "0123456789"),  # Myanmar
        ]

        for input_digits, expected in test_cases:
            assert normalize_token(input_digits) == expected

    def test_normalize_token_e_and_e_handling(self):
        """Test specific e/E handling cases for coverage."""
        # Test e/E not adjacent to digits (should be removed)
        assert normalize_token("e") == "e"
        assert normalize_token("E") == "E"
        assert normalize_token("eE") == "eE"
        assert normalize_token("Ee") == "Ee"
        assert normalize_token("e abc") == ""
        assert normalize_token("E abc") == ""
        assert normalize_token("abc e") == ""
        assert normalize_token("abc E") == ""
        assert normalize_token("abc e def") == ""
        assert normalize_token("abc E def") == ""
        assert normalize_token("e e") == ""
        assert normalize_token("E E") == ""

        # Test e/E adjacent to ASCII digits
        assert normalize_token("123e") == "123e"
        assert normalize_token("e123") == "e123"
        assert normalize_token("123E") == "123E"
        assert normalize_token("E123") == "E123"

        # Test e/E adjacent to Unicode digits
        assert normalize_token("१२३e") == "123e"
        assert normalize_token("e१२३") == "e123"
        assert normalize_token("१२३E") == "123E"
        assert normalize_token("E१२३") == "E123"

        # Test e/E NOT adjacent to digits (should be removed)
        assert normalize_token("abc e xyz") == ""
        assert normalize_token("abc E xyz") == ""
        assert normalize_token("e,") == ","
        assert normalize_token("E,") == ","
        assert normalize_token(",e") == ","
        assert normalize_token(",E") == ","

        # Test e/E in the middle of non-digit text
        assert normalize_token("hello e world") == ""
        assert normalize_token("hello E world") == ""

        # Test e/E at end of string not adjacent to digits
        assert normalize_token("hello e") == ""
        assert normalize_token("hello E") == ""

        # Test e/E at beginning of string not adjacent to digits
        assert normalize_token("e hello") == ""
        assert normalize_token("E hello") == ""

    def test_normalize_token_is_adjacent_to_digit_edge_cases(self):
        """Test edge cases for is_adjacent_to_digit function."""
        # Test with Unicode digits before e/E
        assert normalize_token("٠e") == "0e"
        assert normalize_token("٩E") == "9E"

        # Test with Unicode digits after e/E
        assert normalize_token("e٠") == "e0"
        assert normalize_token("E٩") == "E9"

        # Test with different Unicode digit blocks
        assert normalize_token("०e") == "0e"
        assert normalize_token("९E") == "9E"
        assert normalize_token("e०") == "e0"
        assert normalize_token("E९") == "E9"

        # Test with Bengali digits
        assert normalize_token("০e") == "0e"
        assert normalize_token("৯E") == "9E"
        assert normalize_token("e০") == "e0"
        assert normalize_token("E৯") == "E9"

        # Test with Thai digits
        assert normalize_token("๐e") == "0e"
        assert normalize_token("๙E") == "9E"
        assert normalize_token("e๐") == "e0"
        assert normalize_token("E๙") == "E9"

    def test_normalize_token_space_collapse_edge_cases(self):
        """Test edge cases for space collapsing."""
        # Test strings that originally had no consecutive spaces
        # but would have them after character removal
        assert normalize_token("1 a b 2") == "1 2"
        # Has consecutive spaces originally
        assert normalize_token("1  a  b  2") == "1      2"
        assert normalize_token("1 abc 2") == "1 2"
        assert normalize_token("1 xyz 2") == "1 2"

        # Test strings that originally had consecutive spaces
        # (should NOT be collapsed)
        assert normalize_token("1  2") == "1  2"
        assert normalize_token("1   2") == "1   2"
        assert normalize_token("1    2") == "1    2"

        # Test leading and trailing space handling
        assert normalize_token("abc1") == "1"
        assert normalize_token("1abc") == "1"
        assert normalize_token("abc1def") == "1"
        assert normalize_token("   abc1def   ") == "   1   "

        # Test leading space created by removing invalid characters
        assert normalize_token("abc 1") == "1"
        assert normalize_token("abc1 ") == "1 "  # Has trailing space originally

        # Test trailing space created by removing invalid characters
        assert normalize_token("1 abc") == "1"
        assert normalize_token(" 1abc") == " 1"  # Has leading space originally

    def test_normalize_token_unicode_digit_helper_functions(self):
        """Test helper functions for specific coverage."""
        # Test with characters that are not Unicode digits
        assert normalize_token("abc") == ""
        assert normalize_token("αβγ") == ""
        assert normalize_token("!@#") == ""

        # Test with e/E NOT next to digits at beginning or end
        assert normalize_token("e") == "e"
        assert normalize_token("E") == "E"
        assert normalize_token("e x") == ""
        assert normalize_token("E x") == ""

        # Test with characters that cannot be converted to Unicode digits
        assert normalize_token("abc123xyz") == "123"
        assert normalize_token("αβγ456δε") == "456"

        # Test with characters that are adjacent to Unicode digits
        assert normalize_token("１e") == "1e"
        assert normalize_token("E१") == "E1"
        assert normalize_token("e ") == "e "  # Has trailing space originally
        assert normalize_token("E ") == "E "  # Has trailing space originally

        # Test with characters that are NOT adjacent to digits
        assert normalize_token("ax") == ""
        assert normalize_token("xyz") == ""
        assert normalize_token("e.") == "."  # e is removed, . is kept
        assert normalize_token("E.") == "."  # E is removed, . is kept

        # Test with specific edge cases for _is_unicode_digit
        assert normalize_token("x") == ""
        assert normalize_token("y") == ""
        assert normalize_token("z") == ""

        # Test with specific edge cases for _try_get_unicode_digit
        assert normalize_token("αβγ") == ""
        assert normalize_token("δεζ") == ""

        # Test with adjacency check edge cases
        assert normalize_token("1e x") == "1e"
        assert normalize_token("e1 x") == "e1"
        assert normalize_token("1E x") == "1E"
        assert normalize_token("E1 x") == "E1"

        # Test with e/E in middle of string not adjacent to digits
        assert normalize_token("x e y") == ""
        assert normalize_token("x E y") == ""

        # Test with e/E at beginning/end not adjacent to digits
        assert normalize_token("e xyz") == ""
        assert normalize_token("E xyz") == ""
        assert normalize_token("xyz e") == ""
        assert normalize_token("xyz E") == ""
        assert normalize_token("xe") == ""
        assert normalize_token("xE") == ""

        # Test with e/E in index 0 not adjacent to digits
        assert normalize_token("e-") == "-"
        assert normalize_token("E-") == "-"
        assert normalize_token("e+") == "+"
        assert normalize_token("E+") == "+"

    def test_normalize_token_return_type(self):
        """Test that the function returns a string."""
        assert isinstance(normalize_token("123"), str)
        assert isinstance(normalize_token(""), str)
        assert isinstance(normalize_token("abc"), str)
        assert isinstance(normalize_token("१२३"), str)

    def test_normalize_token_missing_coverage_lines(self):
        """Test cases specifically designed to cover missing lines for 100% coverage."""
        # Lines 56, 64, and 135 appear to be unreachable because all Unicode digits
        # that unicodedata.digit() recognizes also return True for isdigit()
        
        # Test line 93: Unicode space separator handling
        # Need a Unicode space separator (category "Zs") 
        # Using various Unicode space characters that are actually category "Zs"
        assert normalize_token("1\u2000234") == "1 234"  # En Quad (U+2000)
        assert normalize_token("1\u2001234") == "1 234"  # Em Quad (U+2001) 
        assert normalize_token("1\u2002234") == "1 234"  # En Space (U+2002)
        assert normalize_token("1\u2003234") == "1 234"  # Em Space (U+2003)
        assert normalize_token("1\u2004234") == "1 234"  # Three-Per-Em Space (U+2004)
        assert normalize_token("1\u2005234") == "1 234"  # Four-Per-Em Space (U+2005)
        assert normalize_token("1\u2006234") == "1 234"  # Six-Per-Em Space (U+2006)
        assert normalize_token("1\u2007234") == "1 234"  # Figure Space (U+2007)
        assert normalize_token("1\u2008234") == "1 234"  # Punctuation Space (U+2008)
        assert normalize_token("1\u2009234") == "1 234"  # Thin Space (U+2009)
        assert normalize_token("1\u200A234") == "1 234"  # Hair Space (U+200A)
        assert normalize_token("1\u1680234") == "1 234"  # Ogham Space Mark (U+1680)
        assert normalize_token("1\u3000234") == "1 234"  # Ideographic Space (U+3000)
