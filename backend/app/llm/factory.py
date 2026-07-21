"""Build an LLM provider from settings or a per-user stored config."""
from __future__ import annotations

from app.config import settings
from app.llm.base import DisabledProvider, LLMProvider
from app.llm.providers import AnthropicProvider, OllamaProvider, OpenAIProvider

_REGISTRY = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def build_provider(config: dict | None = None) -> LLMProvider:
    """Create a provider.

    ``config`` (from a user's encrypted LLM credential) takes precedence over the
    global environment settings; either may be absent.
    """
    config = config or {}
    provider = config.get("provider") or settings.llm_provider
    model = config.get("model") or settings.llm_model

    if provider == "anthropic":
        return AnthropicProvider(model, api_key=config.get("api_key") or settings.anthropic_api_key)
    if provider == "openai":
        return OpenAIProvider(model, api_key=config.get("api_key") or settings.openai_api_key)
    if provider == "ollama":
        return OllamaProvider(model, base_url=config.get("base_url") or settings.ollama_base_url)
    return DisabledProvider(model)
