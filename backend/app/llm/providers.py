"""Concrete LLM providers: Anthropic Claude, OpenAI, and local Ollama."""
from __future__ import annotations

import httpx

from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in message.content if block.type == "text")


class OpenAIProvider(LLMProvider):
    name = "openai"

    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        resp = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""


class GeminiProvider(LLMProvider):
    """Google Gemini via its OpenAI-compatible endpoint (reuses the openai client)."""

    name = "gemini"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url or self.BASE_URL)
        resp = await client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""


class OllamaProvider(LLMProvider):
    """Local model served by Ollama on the Pi (no API key, runs offline)."""

    name = "ollama"

    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "")
