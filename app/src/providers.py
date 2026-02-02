"""
OpenClaw Lite API Providers

OpenAI and Claude API integrations.
"""

import logging
import uuid
from typing import Any

import anthropic
import openai
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProviderResponse(BaseModel):
    """Standardized response from any provider."""

    id: str
    model: str
    content: str
    provider: str
    usage: dict[str, int]


class OpenAIProvider:
    """OpenAI API provider for simple queries."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key) if api_key else None

    async def generate(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        if not self.client:
            raise RuntimeError("OpenAI API key not configured")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return ProviderResponse(
            id=response.id,
            model=response.model,
            content=response.choices[0].message.content or "",
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        )

    def is_available(self) -> bool:
        return self.client is not None


class ClaudeProvider:
    """Claude API provider for complex queries."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else None

    def _convert_messages(
        self, messages: list[dict[str, Any]]
    ) -> tuple[str | None, list[dict[str, str]]]:
        """Convert OpenAI format to Anthropic format."""
        system_message = None
        converted = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_message = content if not system_message else f"{system_message}\n\n{content}"
            elif role == "assistant":
                converted.append({"role": "assistant", "content": content})
            else:
                converted.append({"role": "user", "content": content})

        # Ensure first message is from user
        if converted and converted[0]["role"] == "assistant":
            converted.insert(0, {"role": "user", "content": "Continue."})

        # Merge consecutive same-role messages
        merged = []
        for msg in converted:
            if merged and merged[-1]["role"] == msg["role"]:
                merged[-1]["content"] += "\n\n" + msg["content"]
            else:
                merged.append(msg)

        return system_message, merged

    async def generate(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> ProviderResponse:
        if not self.client:
            raise RuntimeError("Anthropic API key not configured")

        system_message, converted = self._convert_messages(messages)

        if not converted:
            converted = [{"role": "user", "content": "Hello"}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": converted,
            "temperature": temperature,
        }
        if system_message:
            kwargs["system"] = system_message

        response = await self.client.messages.create(**kwargs)

        content = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )

        return ProviderResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            model=self.model,
            content=content,
            provider="claude",
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
        )

    def is_available(self) -> bool:
        return self.client is not None
