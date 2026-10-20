"""LLM Provider factory."""

from __future__ import annotations

from app.agent.llm.anthropic_provider import AnthropicProvider
from app.agent.llm.base import LLMProvider, LLMResult
from app.agent.llm.groq_provider import GroqProvider
from app.agent.llm.mock_provider import MockProvider
from app.agent.llm.openai_provider import OpenAIProvider
from app.config import get_settings

settings = get_settings()


def get_llm_provider(name: str | None = None) -> LLMProvider:
    """Return an instance of the configured LLM provider (default: 'mock')."""
    provider_name = (name or settings.LLM_PROVIDER or "mock").lower()
    if provider_name == "groq":
        return GroqProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    return MockProvider()


__all__ = [
    "LLMProvider",
    "LLMResult",
    "MockProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GroqProvider",
    "get_llm_provider",
]
