#!/usr/bin/env python3
"""
Keystroke Monitor - Captures keystrokes system-wide for AI text assistance.
Runs as a long-lived process, communicates with Electron via stdout/stdin.

Features:
- System-wide keystroke capture using keyboard library
- Active window tracking using pywin32
- Text buffer maintenance (handles backspaces)
- JSON logging with timestamps - saves complete text after 1-second pause
- Privacy filters for sensitive apps (Google Pay, banking)
- Backtick trigger detection with key suppression
- Double-backtick extension mode detection
"""

import sys
import json
import time
import threading
import os
from datetime import datetime

# keyboard library - supports key suppression on Windows
import keyboard

# pywin32 for active window detection (Windows only)
try:
    import win32gui
    import win32process
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print(json.dumps({"event": "error", "message": "pywin32/psutil not installed. Window tracking disabled."}), flush=True)


# ============== Configuration ==============

# Privacy filter - apps where keystrokes should NOT be captured
PRIVATE_APPS = [
    # Payment apps
    "google pay", "gpay", "phonepe", "paytm", "paypal",
    # Banking
    "bank", "banking", "netbanking", "hdfc", "icici", "sbi", "axis",
    # Password managers
    "lastpass", "1password", "bitwarden", "keepass", "dashlane",
    # Sensitive
    "password", "credential", "vault", "authenticator",
]

# Privacy filter - window titles that indicate sensitive content
PRIVATE_TITLE_KEYWORDS = [
    "password", "sign in", "login", "credential", "payment",
    "banking", "bank account", "credit card", "debit card",
    "cvv", "pin", "otp", "verification code",
]

# Log file path
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keylog.json")

# Pause threshold for logging (seconds)
PAUSE_THRESHOLD = 1.0

# Maximum buffer size (characters) to prevent memory issues
MAX_BUFFER_SIZE = 10000

# Maximum log entries to keep
MAX_LOG_ENTRIES = 500

# Maximum characters per log entry
MAX_ENTRY_LENGTH = 2000

# Window check frequency (every N keystrokes) - performance optimization
WINDOW_CHECK_INTERVAL = 100

# Live mode pause threshold for auto-suggestion (seconds)
LIVE_MODE_PAUSE_THRESHOLD = 1.5

# Minimum characters before live suggestion triggers
LIVE_MODE_MIN_CHARS = 3


# ============== Global State ==============

class KeystrokeState:
    def __init__(self):
        self.buffer = []  # Current text buffer (list of characters)
        self.raw_count = 0  # Raw keystroke count (for backspace calculation)
        self.last_window = ""  # Last active window
        self.last_window_process = ""  # Last active process name
        self.is_private = False  # Whether current window is private
        self.last_trigger_time = 0  # Timestamp of last backtick trigger
        self.last_trigger_had_typing = True  # Whether there was typing since last trigger
        self.running = True  # Whether monitor is running
        self.lock = threading.Lock()  # Thread safety

        # For extension mode tracking
        self.last_ai_output = ""  # Last AI output for extension
        self.extension_context = ""  # Context for extension mode

        # For pause-based logging
        self.last_keystroke_time = 0  # Timestamp of last keystroke
        self.pending_log_text = ""  # Text waiting to be logged
        self.pending_log_window = ""  # Window for pending log

        # Performance: keystroke counter for window check optimization
        self._key_counter = 0

        # Live mode (auto-suggestion on pause)
        self.live_mode_enabled = False
        self.live_suggestion_timer = None
        self.live_suggestion_pending = False  # Prevent duplicate triggers

state = KeystrokeState()


# ============== Window Detection ==============

def get_active_window_info():
    """Get the currently active window title and process name."""
    if not HAS_WIN32:
        return "", ""

    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)

        # Get process name
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            process_name = process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = ""

        return window_title, process_name
    except Exception:
        return "", ""


def is_private_context(window_title, process_name):
    """Check if the current context should be private (no keystroke capture)."""
    title_lower = window_title.lower()

    # Check process name against private apps
    for app in PRIVATE_APPS:
        if app in process_name:
            return True

    # Check window title against private apps
    for app in PRIVATE_APPS:
        if app in title_lower:
            return True

    # Check window title for sensitive keywords
    for keyword in PRIVATE_TITLE_KEYWORDS:
        if keyword in title_lower:
            return True

    return False


def check_window_change():
    """Check if active window has changed. Reset buffer if so."""
    window_title, process_name = get_active_window_info()

    with state.lock:
        # Check if window changed
        if window_title != state.last_window or process_name != state.last_window_process:
            old_window = state.last_window

            # Flush pending log before switching
            if state.pending_log_text:
                # Save in background to not block
                text = state.pending_log_text
                window = state.pending_log_window
                state.pending_log_text = ""
                state.pending_log_window = ""
                threading.Thread(target=save_log_entry, args=(text, window), daemon=True).start()

            state.last_window = window_title
            state.last_window_process = process_name

            # Check privacy
            state.is_private = is_private_context(window_title, process_name)

            # Reset buffer on window change
            state.buffer.clear()
            state.raw_count = 0
            state.last_trigger_had_typing = True
            state.last_ai_output = ""
            state.extension_context = ""

            # Notify Electron of window change
            send_event({
                "event": "window_change",
                "old_window": old_window,
                "new_window": window_title,
                "is_private": state.is_private
            })

            return True

    return False


# ============== Logging ==============

def save_log_entry(text, window):
    """Save a complete text entry to the log file."""
    text = text.strip()
    if not text:
        return

    # Limit entry length
    if len(text) > MAX_ENTRY_LENGTH:
        text = text[:MAX_ENTRY_LENGTH]

    entry = {
        "timestamp": datetime.now().isoformat(),
        "text": text,
        "window": window[:200] if window else ""  # Limit window title length
    }

    try:
        # Read existing log
        existing = []
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
            except (json.JSONDecodeError, IOError):
                existing = []

        # Append new entry
        existing.append(entry)

        # Keep only last N entries (reduced for performance)
        if len(existing) > MAX_LOG_ENTRIES:
            existing = existing[-MAX_LOG_ENTRIES:]

        # Write back (minimal formatting for smaller file)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, separators=(',', ':'))

    except Exception as e:
        send_event({"event": "error", "message": f"Log save failed: {str(e)}"})


def check_pause_and_log():
    """Check if there's been a pause and log the pending text."""
    # Quick check WITHOUT lock first (performance optimization)
    if not state.pending_log_text or state.last_keystroke_time == 0:
        return

    time_since_last = time.time() - state.last_keystroke_time
    if time_since_last < PAUSE_THRESHOLD:
        return

    # Only lock if we're actually going to save
    text = None
    window = None
    with state.lock:
        if state.pending_log_text:  # Double-check after lock
            text = state.pending_log_text
            window = state.pending_log_window
            state.pending_log_text = ""
            state.pending_log_window = ""

    # Save in background thread (don't block main loop)
    if text:
        threading.Thread(target=save_log_entry, args=(text, window), daemon=True).start()


def add_to_pending_log(char):
    """Add a character to the pending log text."""
    with state.lock:
        # Limit pending log size
        if len(state.pending_log_text) >= MAX_ENTRY_LENGTH:
            # Save current and start fresh (in background)
            text = state.pending_log_text
            window = state.pending_log_window
            state.pending_log_text = ""
            threading.Thread(target=save_log_entry, args=(text, window), daemon=True).start()
        state.pending_log_text += char
        state.pending_log_window = state.last_window
        state.last_keystroke_time = time.time()


def backspace_pending_log():
    """Remove last character from pending log."""
    with state.lock:
        if state.pending_log_text:
            state.pending_log_text = state.pending_log_text[:-1]
        state.last_keystroke_time = time.time()


# ============== IPC (Communication with Electron) ==============

def send_event(event_data):
    """Send an event to Electron via stdout."""
    try:
        print(json.dumps(event_data), flush=True)
    except Exception:
        pass


def handle_command(cmd_data):
    """Handle a command from Electron."""
    cmd = cmd_data.get("cmd", "")

    if cmd == "reset":
        # Reset buffer after successful injection
        with state.lock:
            state.buffer.clear()
            state.raw_count = 0
            state.last_trigger_had_typing = True
            # Also clear pending log since text was replaced
            state.pending_log_text = ""
            state.pending_log_window = ""
        send_event({"event": "reset_ack"})

    elif cmd == "set_ai_output":
        # Store AI output for extension mode
        with state.lock:
            state.last_ai_output = cmd_data.get("output", "")
            state.extension_context = cmd_data.get("context", "")
        send_event({"event": "ai_output_set"})

    elif cmd == "get_buffer":
        # Return current buffer (for debugging)
        with state.lock:
            send_event({
                "event": "buffer",
                "buffer": "".join(state.buffer),
                "raw_count": state.raw_count,
                "window": state.last_window
            })

    elif cmd == "shutdown":
        # Flush pending log and exit
        with state.lock:
            if state.pending_log_text:
                save_log_entry(state.pending_log_text, state.pending_log_window)
        state.running = False
        send_event({"event": "shutdown_ack"})

    elif cmd == "ping":
        # Health check
        send_event({"event": "pong"})

    elif cmd == "trigger":
        # Manual trigger from Electron (Ctrl+Alt+Enter)
        handle_backtick()

    elif cmd == "set_live_mode":
        # Toggle live mode (auto-suggestion on pause)
        with state.lock:
            state.live_mode_enabled = cmd_data.get("enabled", False)
        send_event({"event": "live_mode_set", "enabled": state.live_mode_enabled})


def stdin_reader():
    """Read commands from stdin in a separate thread."""
    while state.running:
        try:
            line = sys.stdin.readline()
            if not line:
                # EOF - parent process closed
                state.running = False
                break

            line = line.strip()
            if line:
                try:
                    cmd_data = json.loads(line)
                    handle_command(cmd_data)
                except json.JSONDecodeError:
                    send_event({"event": "error", "message": f"Invalid command: {line}"})
        except Exception as e:
            send_event({"event": "error", "message": f"stdin error: {str(e)}"})
            break


# ============== Live Mode Auto-Trigger ==============

def trigger_live_suggestion():
    """Auto-trigger suggestion after pause in live mode."""
    with state.lock:
        # Check if still valid to trigger
        if not state.live_mode_enabled:
            return
        if state.live_suggestion_pending:
            return
        if len(state.buffer) < LIVE_MODE_MIN_CHARS:
            return

        # Mark as pending to prevent duplicates
        state.live_suggestion_pending = True

        # Get buffer content (limit size)
        if len(state.buffer) > 5000:
            buffer_text = "".join(state.buffer[-5000:])
        else:
            buffer_text = "".join(state.buffer)

        char_count = state.raw_count

        # Send live trigger event to Electron
        send_event({
            "event": "trigger",
            "type": "live",
            "buffer": buffer_text,
            "char_count": char_count,
            "window": state.last_window
        })


def cancel_live_timer():
    """Cancel any pending live suggestion timer."""
    if state.live_suggestion_timer:
        state.live_suggestion_timer.cancel()
        state.live_suggestion_timer = None


def start_live_timer():
    """Start timer for live mode auto-suggestion."""
    if not state.live_mode_enabled:
        return

    # Cancel existing timer
    cancel_live_timer()

    # Reset pending flag when starting new timer
    state.live_suggestion_pending = False

    # Start new timer
    state.live_suggestion_timer = threading.Timer(
        LIVE_MODE_PAUSE_THRESHOLD,
        trigger_live_suggestion
    )
    state.live_suggestion_timer.daemon = True
    state.live_suggestion_timer.start()


# ============== Keystroke Handling ==============

def handle_backtick():
    """Handle backtick (`) trigger for AI suggestion."""
    current_time = time.time()

    with state.lock:
        # Check if this is a double-trigger (extension mode)
        # Conditions: Less than 2 seconds since last trigger AND no typing between
        time_since_last = current_time - state.last_trigger_time
        is_extension = (time_since_last < 2.0) and (not state.last_trigger_had_typing)

        # Update trigger state
        state.last_trigger_time = current_time
        state.last_trigger_had_typing = False

        # Get buffer content (limit size for performance)
        if len(state.buffer) > 5000:
            buffer_text = "".join(state.buffer[-5000:])  # Last 5000 chars only
        else:
            buffer_text = "".join(state.buffer)

        char_count = state.raw_count

        # Determine trigger type
        trigger_type = "extension" if is_extension else "backtick"

        # For extension mode, include last AI output
        event_data = {
            "event": "trigger",
            "type": trigger_type,
            "buffer": buffer_text,
            "char_count": char_count,
            "window": state.last_window
        }

        if is_extension:
            event_data["last_ai_output"] = state.last_ai_output
            event_data["extension_context"] = state.extension_context

        # Send event to Electron
        send_event(event_data)


def on_key_event(event):
    """Handle keyboard events."""
    if not state.running:
        return

    # Only process key down events
    if event.event_type != keyboard.KEY_DOWN:
        return

    # Performance: Only check window every N keystrokes
    state._key_counter += 1
    if state._key_counter >= WINDOW_CHECK_INTERVAL:
        state._key_counter = 0
        check_window_change()

    # Skip if in private context
    if state.is_private:
        return

    key_name = event.name

    try:
        # Handle special keys
        if key_name == 'backspace':
            with state.lock:
                if state.buffer:
                    state.buffer.pop()
                state.raw_count += 1
                state.last_trigger_had_typing = True
                state.live_suggestion_pending = False  # Reset on edit
            backspace_pending_log()
            start_live_timer()  # Restart timer

        elif key_name == 'enter':
            with state.lock:
                state.buffer.append('\n')
                state.raw_count += 1
                state.last_trigger_had_typing = True
                state.live_suggestion_pending = False
            add_to_pending_log('\n')
            cancel_live_timer()  # Don't trigger on enter

        elif key_name == 'space':
            with state.lock:
                state.buffer.append(' ')
                state.raw_count += 1
                state.last_trigger_had_typing = True
                state.live_suggestion_pending = False
            add_to_pending_log(' ')
            start_live_timer()  # Restart timer

        elif key_name == 'tab':
            with state.lock:
                state.buffer.append('\t')
                state.raw_count += 1
                state.last_trigger_had_typing = True
                state.live_suggestion_pending = False
            add_to_pending_log('\t')
            start_live_timer()  # Restart timer

        elif len(key_name) == 1:
            # Regular character (but not backtick - handled separately)
            if key_name != '`':
                with state.lock:
                    # Limit buffer size to prevent memory issues
                    if len(state.buffer) >= MAX_BUFFER_SIZE:
                        # Remove oldest characters
                        state.buffer = state.buffer[-(MAX_BUFFER_SIZE - 1):]
                    state.buffer.append(key_name)
                    state.raw_count += 1
                    state.last_trigger_had_typing = True
                    state.live_suggestion_pending = False
                add_to_pending_log(key_name)
                start_live_timer()  # Restart timer on character

        # Ignore other special keys (shift, ctrl, alt, etc.)

    except Exception as e:
        send_event({"event": "error", "message": f"on_key_event error: {str(e)}"})


# ============== Pause Monitor Thread ==============

def pause_monitor():
    """Periodically check for typing pauses to save logs."""
    while state.running:
        check_pause_and_log()
        time.sleep(0.5)  # Check every 500ms (optimized from 200ms)


# ============== Window Monitor Thread ==============

def window_monitor():
    """Periodically check for window changes."""
    while state.running:
        check_window_change()
        time.sleep(1.0)  # Check every 1 second (optimized from 500ms)


# ============== Main ==============

def main():
    """Main entry point."""
    send_event({"event": "started", "pid": os.getpid()})

    # Start stdin reader thread
    stdin_thread = threading.Thread(target=stdin_reader, daemon=True)
    stdin_thread.start()

    # Start window monitor thread
    window_thread = threading.Thread(target=window_monitor, daemon=True)
    window_thread.start()

    # Start pause monitor thread for logging
    pause_thread = threading.Thread(target=pause_monitor, daemon=True)
    pause_thread.start()

    # Initial window check
    check_window_change()

    # Hook all keyboard events
    keyboard.hook(on_key_event)

    try:
        # Keep running until state.running is False
        while state.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        keyboard.unhook_all()
        cancel_live_timer()  # Cancel any pending live timer
        # Flush any pending log
        with state.lock:
            if state.pending_log_text:
                save_log_entry(state.pending_log_text, state.pending_log_window)
        send_event({"event": "stopped"})


if __name__ == "__main__":
    main()
