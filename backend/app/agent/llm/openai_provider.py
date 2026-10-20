"""OpenAI LLM Provider implementation using httpx."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.agent.llm.base import LLMProvider, LLMResult
from app.config import get_settings
from app.core.errors import AppError, ErrorCode

settings = get_settings()


class OpenAIProvider(LLMProvider):
    """Provider integrating with OpenAI Chat Completions API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or (settings.OPENAI_MODEL if settings.OPENAI_MODEL != "REPLACE_ME" else "gpt-4o-mini")

    async def complete(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        if not self.api_key or self.api_key == "REPLACE_ME":
            raise AppError(
                code=ErrorCode.LLM_ERROR,
                message="OpenAI API key is not configured.",
                status_code=500,
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        if json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": json_schema,
                },
            }

        start_t = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)

            if resp.status_code != 200:
                raise AppError(
                    code=ErrorCode.LLM_ERROR,
                    message=f"OpenAI error {resp.status_code}: {resp.text}",
                    status_code=502,
                )

            data = resp.json()
            choice = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)

            return LLMResult(
                text=choice,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=elapsed_ms,
            )
