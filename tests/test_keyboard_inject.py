"""Tests for keyboard_inject.py - unescape_text, get_typing_delay, get_typo_char, constants."""
import pytest
from keyboard_inject import (
    unescape_text,
    get_typing_delay,
    get_typo_char,
    SHIFT_CHARS,
    SPECIAL_KEYS,
)


class TestUnescapeText:
    def test_unescape_newline(self):
        assert unescape_text("a\\nb") == "a\nb"

    def test_unescape_tab(self):
        assert "\t" in unescape_text("a\\tb") or "    " in unescape_text("a\\tb")


class TestGetTypingDelay:
    def test_fast_mode_returns_small_delay(self):
        d = get_typing_delay(humanize=False)
        assert d <= 0.01

    def test_humanize_returns_positive_delay(self):
        for _ in range(5):
            d = get_typing_delay(humanize=True)
            assert d > 0


class TestGetTypoChar:
    def test_typo_char_for_letter_returns_adjacent_or_same(self):
        result = get_typo_char("a")
        assert result in "asqw" or result == "a"

    def test_typo_char_preserves_uppercase(self):
        result = get_typo_char("A")
        assert result.isupper() or result == "A"


class TestConstants:
    def test_shift_chars_has_common_symbols(self):
        assert "!" in SHIFT_CHARS
        assert SHIFT_CHARS["!"] == "1"

    def test_special_keys_has_newline_and_tab(self):
        assert "\n" in SPECIAL_KEYS
        assert "\t" in SPECIAL_KEYS or "\r" in SPECIAL_KEYS
