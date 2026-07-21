"""Pluggable LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Minimal text-generation interface all providers implement."""

    name: str = "base"

    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        ...


class DisabledProvider(LLMProvider):
    name = "none"

    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        raise RuntimeError(
            "LLM analysis is not configured. Set a provider and API key on the Settings page."
        )
