"""Tests for ai_backend_service.py - API key loading, clean_response, build_messages, handle_request."""
import json
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

# Import after path setup
import ai_backend_service as svc


class TestLoadApiKey:
    """Test load_api_key from environment and config files."""

    def test_load_api_key_from_env(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "env-key-123"}, clear=False):
            assert svc.load_api_key() == "env-key-123"

    def test_load_api_key_returns_none_when_missing(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": ""}, clear=False):
            with patch("os.path.exists", return_value=False):
                assert svc.load_api_key() is None

    def test_load_api_key_from_file_skips_your_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", MagicMock(return_value=StringIO("MISTRAL_API_KEY=your-api-key-here"))):
                    key = svc.load_api_key()
                    assert key is None


class TestCleanResponse:
    """Test clean_response strips subject lines and normalizes text."""

    def test_clean_response_empty(self):
        assert svc.clean_response("") == ""
        assert svc.clean_response(None) == ""

    def test_clean_response_strips_subject_line_and_next_blank(self):
        text = "Subject: Hello\n\nBody line one.\nBody line two."
        assert "Subject:" not in svc.clean_response(text)
        assert "Body line one" in svc.clean_response(text)

    def test_clean_response_preserves_normal_lines(self):
        text = "Line one.\nLine two.\nLine three."
        assert svc.clean_response(text) == text

    def test_clean_response_strips_whitespace(self):
        text = "  Hello world  \n  Second line  "
        assert svc.clean_response(text).strip() == svc.clean_response(text)


class TestBuildMessages:
    """Test build_messages for each mode."""

    def test_build_messages_backtick_mode(self):
        messages = svc.build_messages("fix this sentance", {"mode": "backtick"})
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "autocorrect" in messages[0]["content"].lower()
        assert messages[1]["content"] == "fix this sentance"

    def test_build_messages_extension_mode_includes_last_output(self):
        messages = svc.build_messages("original", {"mode": "extension", "last_output": "Previous text."})
        assert len(messages) == 1
        assert "Previous text." in messages[0]["content"]
        assert "original" in messages[0]["content"]

    def test_build_messages_clipboard_mode(self):
        messages = svc.build_messages("two sum problem", {"mode": "clipboard"})
        assert len(messages) == 2
        assert "CODE" in messages[0]["content"] or "clipboard" in messages[0]["content"].lower()

    def test_build_messages_prompt_mode_default_tone(self):
        messages = svc.build_messages("Write a greeting", {"mode": "prompt"})
        assert len(messages) == 1
        assert "professional" in messages[0]["content"].lower() or "TONE" in messages[0]["content"]

    def test_build_messages_explanation_mode_includes_code(self):
        messages = svc.build_messages("two sum", {"mode": "explanation", "code": "def two_sum(): pass"})
        assert len(messages) == 2
        assert "def two_sum" in messages[1]["content"]
        assert "Explain" in messages[0]["content"] or "interview" in messages[0]["content"].lower()


class TestHandleRequest:
    """Test handle_request command routing (with mocked client and IPC)."""

    def test_handle_request_ping_sends_pong(self):
        with patch.object(svc.IPC, "send") as mock_send:
            svc.handle_request({"cmd": "ping"}, MagicMock())
            mock_send.assert_called()
            call_arg = mock_send.call_args[0][0]
            assert call_arg.get("event") == "pong"

    def test_handle_request_unknown_command_sends_error(self):
        with patch.object(svc.IPC, "send_error") as mock_err:
            svc.handle_request({"cmd": "unknown_cmd"}, MagicMock())
            mock_err.assert_called_once()
            assert "Unknown command" in mock_err.call_args[0][0]

    def test_handle_request_generate_empty_prompt_sends_complete_with_error(self):
        with patch.object(svc.IPC, "send") as mock_send:
            svc.handle_request({"cmd": "generate", "prompt": "", "context": {}}, MagicMock())
            call_arg = mock_send.call_args[0][0]
            assert call_arg.get("event") == "complete"
            assert "error" in call_arg or call_arg.get("text") == ""
