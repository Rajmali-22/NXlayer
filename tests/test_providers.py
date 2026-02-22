"""Tests for providers package — ProviderManager, router, and model resolution."""
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

from providers import ProviderManager
from providers.router import (
    discover_available_models,
    get_available_agents,
    pick_model_for_group,
    pick_model_for_group_excluding,
    pick_specific_model,
    PROVIDER_REGISTRY,
    GROUP_FALLBACK_ORDER,
)


class TestDiscoverAvailableModels:
    """Test auto-discovery of available models from env vars."""

    def test_no_keys_returns_empty_groups(self):
        with patch.dict(os.environ, {}, clear=True):
            available = discover_available_models()
            assert available["fast"] == []
            assert available["powerful"] == []
            assert available["reasoning"] == []

    def test_single_key_discovered(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test123"}, clear=True):
            available = discover_available_models()
            assert len(available["fast"]) >= 1
            model_strings = [m[0] for m in available["fast"]]
            assert "groq/llama-3.3-70b-versatile" in model_strings

    def test_placeholder_key_ignored(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "your-groq-key-here"}, clear=True):
            available = discover_available_models()
            assert available["fast"] == []

    def test_multiple_keys_discovered(self):
        env = {
            "GROQ_API_KEY": "gsk_test",
            "MISTRAL_API_KEY": "msk_test",
            "DEEPSEEK_API_KEY": "dsk_test",
        }
        with patch.dict(os.environ, env, clear=True):
            available = discover_available_models()
            assert len(available["fast"]) >= 2  # groq + mistral
            assert len(available["powerful"]) >= 1  # deepseek

    def test_deepseek_appears_in_both_powerful_and_reasoning(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "dsk_test"}, clear=True):
            available = discover_available_models()
            powerful_models = [m[0] for m in available["powerful"]]
            reasoning_models = [m[0] for m in available["reasoning"]]
            assert "deepseek/deepseek-chat" in powerful_models
            assert "deepseek/deepseek-reasoner" in reasoning_models


class TestGetAvailableAgents:
    """Test agent list generation for UI dropdown."""

    def test_always_includes_auto(self):
        with patch.dict(os.environ, {}, clear=True):
            agents = get_available_agents()
            assert agents[0]["value"] == "auto"
            assert agents[0]["label"] == "Auto"

    def test_includes_configured_models(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            agents = get_available_agents()
            values = [a["value"] for a in agents]
            assert "groq/llama-3.3-70b-versatile" in values


class TestPickModelForGroup:
    """Test model selection by group with fallback."""

    def test_picks_first_in_group(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test", "MISTRAL_API_KEY": "msk_test"}, clear=True):
            model = pick_model_for_group("fast")
            assert model is not None
            assert "groq/" in model or "mistral/" in model

    def test_fallback_to_another_group(self):
        # Only powerful available, requesting fast → should fallback to powerful
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "dsk_test"}, clear=True):
            model = pick_model_for_group("fast")
            assert model is not None
            assert "deepseek/" in model

    def test_returns_none_when_no_providers(self):
        with patch.dict(os.environ, {}, clear=True):
            model = pick_model_for_group("fast")
            assert model is None


class TestPickSpecificModel:
    """Test specific model validation."""

    def test_valid_model_with_key(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            result = pick_specific_model("groq/llama-3.3-70b-versatile")
            assert result == "groq/llama-3.3-70b-versatile"

    def test_valid_model_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = pick_specific_model("groq/llama-3.3-70b-versatile")
            assert result is None

    def test_unknown_model_passed_through(self):
        result = pick_specific_model("custom/my-model")
        assert result == "custom/my-model"


class TestProviderManager:
    """Test ProviderManager initialization and methods."""

    def test_init_with_no_keys(self):
        with patch.dict(os.environ, {}, clear=True):
            pm = ProviderManager()
            assert not pm.has_any_provider()

    def test_init_with_key(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            pm = ProviderManager()
            assert pm.has_any_provider()

    def test_resolve_model_auto(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            pm = ProviderManager()
            model = pm.resolve_model(agent="auto", mode="backtick")
            assert model is not None

    def test_resolve_model_specific(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            pm = ProviderManager()
            model = pm.resolve_model(agent="groq/llama-3.3-70b-versatile")
            assert model == "groq/llama-3.3-70b-versatile"

    def test_get_model_group(self):
        pm = ProviderManager.__new__(ProviderManager)
        pm.available = {}
        pm.memory = MagicMock()
        assert pm.get_model_group("groq/llama-3.3-70b-versatile") == "fast"
        assert pm.get_model_group("deepseek/deepseek-chat") == "powerful"
        assert pm.get_model_group("deepseek/deepseek-reasoner") == "reasoning"
        assert pm.get_model_group("unknown/model") == "powerful"  # default

    def test_get_available_agents_returns_list(self):
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "msk_test"}, clear=True):
            pm = ProviderManager()
            agents = pm.get_available_agents()
            assert isinstance(agents, list)
            assert len(agents) >= 1
            assert agents[0]["value"] == "auto"


class TestFallbackOnAuthError:
    """Test that failed models are skipped and fallback works."""

    def test_fallback_skips_failed_model(self):
        env = {"DEEPSEEK_API_KEY": "dsk_test", "GROQ_API_KEY": "gsk_test"}
        with patch.dict(os.environ, env, clear=True):
            pm = ProviderManager()
            # Simulate auth failure on deepseek
            fallback = pm.get_fallback_model("deepseek/deepseek-chat")
            assert fallback is not None
            assert fallback != "deepseek/deepseek-chat"

    def test_fallback_returns_none_when_all_failed(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test"}, clear=True):
            pm = ProviderManager()
            pm.mark_model_failed("groq/llama-3.3-70b-versatile")
            fallback = pm.get_fallback_model("groq/llama-3.3-70b-versatile")
            assert fallback is None

    def test_fallback_crosses_groups(self):
        env = {"DEEPSEEK_API_KEY": "dsk_test", "GROQ_API_KEY": "gsk_test"}
        with patch.dict(os.environ, env, clear=True):
            pm = ProviderManager()
            # Fail all powerful models — should fall back to fast group
            pm.mark_model_failed("deepseek/deepseek-chat")
            fallback = pm.get_fallback_model("deepseek/deepseek-chat")
            assert fallback is not None
            # Should get groq (fast group)
            assert "groq/" in fallback

    def test_pick_model_for_group_excluding(self):
        env = {"DEEPSEEK_API_KEY": "dsk_test", "ANTHROPIC_API_KEY": "sk_test"}
        with patch.dict(os.environ, env, clear=True):
            # Exclude deepseek, should get anthropic
            model = pick_model_for_group_excluding(
                "powerful",
                {"deepseek/deepseek-chat"}
            )
            assert model is not None
            assert model != "deepseek/deepseek-chat"
