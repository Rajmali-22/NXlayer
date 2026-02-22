"""Tests for providers.memory — MemoryManager per-window sessions."""
import os
import json
import time
import shutil
import tempfile

import pytest

from providers.memory import MemoryManager, _normalize_window_title, SKIP_MEMORY_MODES


class TestNormalizeWindowTitle:
    """Test window title normalization."""

    def test_vscode_title(self):
        assert _normalize_window_title("file.py - VS Code") == "vs_code"

    def test_chrome_title(self):
        assert _normalize_window_title("Google Chrome") == "google_chrome"

    def test_complex_title(self):
        result = _normalize_window_title("index.js - project - Visual Studio Code")
        assert result == "visual_studio_code"

    def test_empty_title(self):
        assert _normalize_window_title("") == "unknown"
        assert _normalize_window_title(None) == "unknown"

    def test_simple_app(self):
        assert _normalize_window_title("Terminal") == "terminal"


class TestMemoryManager:
    """Test MemoryManager with a temp directory."""

    @pytest.fixture
    def tmp_sessions(self, tmp_path):
        return str(tmp_path / "sessions")

    @pytest.fixture
    def mm(self, tmp_sessions):
        return MemoryManager(sessions_dir=tmp_sessions)

    def test_init_creates_dir(self, mm, tmp_sessions):
        assert os.path.isdir(tmp_sessions)

    def test_store_and_retrieve(self, mm):
        mm.store_interaction("file.py - VS Code", "hello", "hi there", "powerful")
        history = mm.get_history("file.py - VS Code", "powerful")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "hi there"

    def test_backtick_mode_skipped(self, mm):
        mm.store_interaction("Terminal", "fix this", "fixed", "fast", mode="backtick")
        history = mm.get_history("Terminal", "fast", mode="backtick")
        assert history == []

    def test_live_mode_skipped(self, mm):
        mm.store_interaction("Terminal", "fix this", "fixed", "fast", mode="live")
        history = mm.get_history("Terminal", "fast", mode="live")
        assert history == []

    def test_fast_group_prompt_mode_has_memory(self, mm):
        mm.store_interaction("Terminal", "my name is Raj", "Nice to meet you Raj", "fast", mode="prompt")
        history = mm.get_history("Terminal", "fast", mode="prompt")
        assert len(history) == 2

    def test_same_window_different_titles(self, mm):
        mm.store_interaction("a.py - VS Code", "q1", "a1", "powerful")
        mm.store_interaction("b.py - VS Code", "q2", "a2", "powerful")
        history = mm.get_history("c.py - VS Code", "powerful")
        assert len(history) == 4  # all same session key "vs_code"

    def test_different_windows(self, mm):
        mm.store_interaction("file.py - VS Code", "q1", "a1", "powerful")
        mm.store_interaction("Google Chrome", "q2", "a2", "powerful")
        vs_history = mm.get_history("file.py - VS Code", "powerful")
        chrome_history = mm.get_history("Google Chrome", "powerful")
        assert len(vs_history) == 2
        assert len(chrome_history) == 2

    def test_max_history_truncation(self, mm):
        for i in range(15):
            mm.store_interaction("Terminal - VS Code", f"q{i}", f"a{i}", "powerful")
        history = mm.get_history("Terminal - VS Code", "powerful")
        # MAX_HISTORY_PER_SESSION=10, each exchange = 2 msgs → 20 msgs max
        assert len(history) <= 20

    def test_persistence(self, tmp_sessions):
        mm1 = MemoryManager(sessions_dir=tmp_sessions)
        mm1.store_interaction("file.py - VS Code", "hello", "world", "powerful")

        # Create new instance — should load from disk
        mm2 = MemoryManager(sessions_dir=tmp_sessions)
        history = mm2.get_history("file.py - VS Code", "powerful")
        assert len(history) == 2
        assert history[0]["content"] == "hello"

    def test_clear_session(self, mm):
        mm.store_interaction("file.py - VS Code", "q1", "a1", "powerful")
        mm.clear_session("file.py - VS Code")
        history = mm.get_history("file.py - VS Code", "powerful")
        assert history == []

    def test_prune_old_sessions(self, tmp_sessions):
        mm = MemoryManager(sessions_dir=tmp_sessions)
        # Manually write an old session
        old_data = [
            {"role": "user", "content": "old", "ts": time.time() - 8 * 86400},
            {"role": "assistant", "content": "data", "ts": time.time() - 8 * 86400},
        ]
        os.makedirs(tmp_sessions, exist_ok=True)
        with open(os.path.join(tmp_sessions, "old_app.json"), "w") as f:
            json.dump(old_data, f)

        # Re-init to trigger pruning
        mm2 = MemoryManager(sessions_dir=tmp_sessions)
        assert "old_app" not in mm2.sessions

    def test_reasoning_group_uses_memory(self, mm):
        mm.store_interaction("file.py - VS Code", "explain", "explanation", "reasoning")
        history = mm.get_history("file.py - VS Code", "reasoning")
        assert len(history) == 2
