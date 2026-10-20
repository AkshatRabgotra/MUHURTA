"""Groq LLM Provider implementation using httpx."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.agent.llm.base import LLMProvider, LLMResult
from app.config import get_settings
from app.core.errors import AppError, ErrorCode

settings = get_settings()


class GroqProvider(LLMProvider):
    """Provider integrating with Groq's high-speed Llama models API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or (settings.GROQ_MODEL if settings.GROQ_MODEL != "REPLACE_ME" else "llama-3.3-70b-versatile")

    async def complete(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResult:
        if not self.api_key or self.api_key == "REPLACE_ME":
            raise AppError(
                code=ErrorCode.LLM_ERROR,
                message="Groq API key is not configured.",
                status_code=500,
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        formatted_messages = [dict(m) for m in messages]

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.2,
        }

        if json_schema is not None:
            # Groq JSON mode
            payload["response_format"] = {"type": "json_object"}
            schema_instruction = f"\nYou MUST respond with valid JSON strictly conforming to this schema:\n{json.dumps(json_schema)}"
            # Inject instruction into system message or append
            if formatted_messages and formatted_messages[0]["role"] == "system":
                formatted_messages[0]["content"] += schema_instruction
            else:
                formatted_messages.append({"role": "system", "content": schema_instruction})

        start_t = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)

            if resp.status_code != 200:
                raise AppError(
                    code=ErrorCode.LLM_ERROR,
                    message=f"Groq error {resp.status_code}: {resp.text}",
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
