"""Tests for smart_prompts.py - detect_text_type, build_prompt, clean_output."""
import pytest
from smart_prompts import detect_text_type, build_prompt, clean_output


class TestDetectTextType:
    """Test text type detection for clipboard/smart prompts."""

    def test_detect_email_by_greeting(self):
        text = "Dear John,\n\nThank you for your email. I will get back to you."
        cat, sub = detect_text_type(text)
        assert cat == "email"

    def test_detect_system_design(self):
        text = "Design a URL shortener for 1 million users with high availability."
        cat, sub = detect_text_type(text)
        assert cat == "system_design"

    def test_detect_behavioral(self):
        text = "Tell me about a time when you had a conflict with a teammate."
        cat, sub = detect_text_type(text)
        assert cat == "behavioral"

    def test_detect_code_problem_dp(self):
        text = "Coin change problem dynamic programming"
        cat, sub = detect_text_type(text)
        assert cat == "code_problem"
        assert sub == "dp"

    def test_detect_code_problem_two_sum(self):
        text = "two sum leetcode"
        cat, sub = detect_text_type(text)
        assert cat == "code_problem"

    def test_detect_term_short_no_question(self):
        text = "OOP"
        cat, sub = detect_text_type(text)
        assert cat == "term"

    def test_detect_question(self):
        text = "What is REST API?"
        cat, sub = detect_text_type(text)
        assert cat == "question"

    def test_detect_general_fallback(self):
        text = "Improve this sentence for better clarity and flow."
        cat, sub = detect_text_type(text)
        assert cat == "general"


class TestBuildPrompt:
    """Test build_prompt with custom instruction and auto-detect."""

    def test_build_prompt_with_custom_instruction(self):
        sys_prompt, user_prompt = build_prompt("some code here", user_instruction="explain in one line", mode="clipboard")
        assert "custom" in sys_prompt.lower() or "instruction" in user_prompt.lower()
        assert "explain in one line" in user_prompt
        assert "some code here" in user_prompt

    def test_build_prompt_auto_detect_question(self):
        sys_prompt, user_prompt = build_prompt("What is dependency injection?")
        assert "question" in sys_prompt.lower() or "answer" in sys_prompt.lower()
        assert "dependency injection" in user_prompt


class TestCleanOutput:
    """Test clean_output removes markdown and preambles."""

    def test_clean_output_removes_code_fence(self):
        text = "```python\ndef foo(): pass\n```"
        out = clean_output(text)
        assert "```" not in out

    def test_clean_output_removes_bold(self):
        text = "**Important** point here."
        out = clean_output(text)
        assert "**" not in out

    def test_clean_output_removes_here_is_preamble(self):
        text = "Here's the solution:\nActual content."
        out = clean_output(text)
        assert out.strip().startswith("Actual") or "Here's" not in out

    def test_clean_output_empty_and_none(self):
        assert clean_output("") == ""
        assert clean_output(None) is None
