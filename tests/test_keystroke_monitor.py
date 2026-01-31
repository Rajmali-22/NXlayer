"""Tests for keystroke_monitor state and config."""
import pytest
from keystroke_monitor.state import State
from keystroke_monitor.config import Config


class TestState:
    def test_reset_buffer_clears_buffer_and_extension(self):
        state = State()
        state.buffer = ["a", "b", "c"]
        state.last_ai_output = "output"
        state.extension_context = "ctx"
        state.reset_buffer()
        assert len(state.buffer) == 0
        assert state.last_ai_output == ""
        assert state.extension_context == ""


class TestConfig:
    def test_config_has_required_constants(self):
        assert Config.MAX_BUFFER_SIZE > 0
        assert Config.MAX_LOG_ENTRIES > 0
        assert Config.LOG_FILE.endswith(".json")
        assert len(Config.PRIVATE_APPS) > 0
