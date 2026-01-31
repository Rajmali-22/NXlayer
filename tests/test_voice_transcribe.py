"""Tests for voice_transcribe.py - transcribe_audio error handling."""
from unittest.mock import MagicMock, patch
import speech_recognition as sr
import voice_transcribe as vt


class TestTranscribeAudio:
    def test_transcribe_audio_returns_error_on_unknown_value(self):
        mock_audio = MagicMock()
        recognizer = sr.Recognizer()
        with patch.object(recognizer, "recognize_google", side_effect=sr.UnknownValueError()):
            result = vt.transcribe_audio(mock_audio, recognizer)
        assert isinstance(result, dict)
        assert "error" in result
        assert "Could not understand" in result.get("error", "")

    def test_transcribe_audio_returns_dict_with_text_on_success(self):
        mock_audio = MagicMock()
        recognizer = sr.Recognizer()
        with patch.object(recognizer, "recognize_google", return_value="Hello world"):
            result = vt.transcribe_audio(mock_audio, recognizer)
        assert result == {"text": "Hello world"}
