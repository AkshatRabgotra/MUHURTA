"""Anthropic LLM Provider implementation using httpx."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.agent.llm.base import LLMProvider, LLMResult
from app.config import get_settings
from app.core.errors import AppError, ErrorCode

settings = get_settings()


class AnthropicProvider(LLMProvider):
    """Provider integrating with Anthropic Messages API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or (settings.ANTHROPIC_MODEL if settings.ANTHROPIC_MODEL != "REPLACE_ME" else "claude-3-5-haiku-latest")

    async def complete(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        if not self.api_key or self.api_key == "REPLACE_ME":
            raise AppError(
                code=ErrorCode.LLM_ERROR,
                message="Anthropic API key is not configured.",
                status_code=500,
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Separate system messages from user/assistant
        system_prompts: list[str] = []
        anthropic_messages: list[dict[str, str]] = []

        for m in messages:
            if m.get("role") == "system":
                system_prompts.append(m.get("content", ""))
            else:
                anthropic_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        if json_schema is not None:
            system_prompts.append(
                f"You MUST respond ONLY with valid JSON conforming to this schema:\n{json.dumps(json_schema)}\nDo not include backticks, markdown, or text outside the JSON."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": anthropic_messages,
            "temperature": 0.2,
        }
        if system_prompts:
            payload["system"] = "\n\n".join(system_prompts)

        start_t = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)

            if resp.status_code != 200:
                raise AppError(
                    code=ErrorCode.LLM_ERROR,
                    message=f"Anthropic error {resp.status_code}: {resp.text}",
                    status_code=502,
                )

            data = resp.json()
            content_blocks = data.get("content", [])
            choice = content_blocks[0].get("text", "") if content_blocks else ""
            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

            return LLMResult(
                text=choice,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
            )
