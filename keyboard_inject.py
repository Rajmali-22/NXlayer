#!/usr/bin/env python3
"""
Keyboard injection module using pynput - pure Python, no Rust.
Replaces keyboard-inject/src/main.rs functionality.
"""

import sys
import time
from pynput.keyboard import Controller, Key

keyboard = Controller()

# Mapping for special characters that need shift
SHIFT_CHARS = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
    ':': ';', '"': "'", '<': ',', '>': '.', '?': '/',
    '~': '`'
}

# Special keys mapping
SPECIAL_KEYS = {
    '\n': Key.enter,
    '\r': Key.enter,
    '\t': Key.tab,
}


def unescape_text(text):
    """Convert escape sequences to actual characters."""
    return (text
            .replace('\\n', '\n')
            .replace('\\r', '\r')
            .replace('\\t', '    ')  # Convert tabs to 4 spaces (avoid field navigation)
            .replace('\t', '    '))


def send_char(char):
    """Send a single character using keyboard simulation."""
    # Handle special keys
    if char in SPECIAL_KEYS:
        keyboard.press(SPECIAL_KEYS[char])
        keyboard.release(SPECIAL_KEYS[char])
        return

    # Handle shifted characters
    if char in SHIFT_CHARS:
        keyboard.press(Key.shift)
        keyboard.press(SHIFT_CHARS[char])
        keyboard.release(SHIFT_CHARS[char])
        keyboard.release(Key.shift)
        return

    # Handle uppercase letters
    if char.isupper():
        keyboard.press(Key.shift)
        keyboard.press(char.lower())
        keyboard.release(char.lower())
        keyboard.release(Key.shift)
        return

    # Regular character - just type it
    try:
        keyboard.press(char)
        keyboard.release(char)
    except Exception:
        # Fallback: use type() for unicode characters
        keyboard.type(char)


def send_text(text):
    """Send text character by character with proper timing."""
    # Small delay to ensure target window is ready
    time.sleep(0.05)

    for char in text:
        send_char(char)
        # Minimal delay between characters (1ms for speed)
        time.sleep(0.001)


def send_backspaces(count):
    """Send a number of backspace key presses to delete text."""
    if count <= 0:
        return

    # Small delay before starting
    time.sleep(0.05)

    for _ in range(count):
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)
        # Slightly longer delay for backspaces to ensure they register
        time.sleep(0.002)

    # Small delay after backspaces before typing new text
    time.sleep(0.05)


def main():
    if len(sys.argv) < 2:
        print("Usage: python keyboard_inject.py <text> [--backspace N]", file=sys.stderr)
        sys.exit(1)

    # Parse arguments
    text = sys.argv[1]
    backspace_count = 0

    # Check for --backspace flag
    if len(sys.argv) >= 4 and sys.argv[2] == '--backspace':
        try:
            backspace_count = int(sys.argv[3])
        except ValueError:
            print("Invalid backspace count", file=sys.stderr)
            backspace_count = 0

    # Unescape newlines and other escape sequences
    text = unescape_text(text)

    # Send backspaces first to delete old text
    if backspace_count > 0:
        send_backspaces(backspace_count)

    # Split by actual newlines and send each line
    lines = text.split('\n')

    for i, line in enumerate(lines):
        if line:
            send_text(line)

        # Press Enter after each line except the last
        if i < len(lines) - 1:
            keyboard.press(Key.enter)
            keyboard.release(Key.enter)
            time.sleep(0.01)


if __name__ == '__main__':
    main()
